import contextlib
import logging
import os
from typing import Optional

from pytest_embedded.log import MessageQueue, live_print_call
from pytest_embedded_idf.app import FlashFile, IdfApp

from . import DEFAULT_IMAGE_FN, ENCRYPTED_IMAGE_FN


class IdfFlashImageMaker:
    """
    Create a single image for QEMU based on the `IdfApp`'s partition table and all the flash files.
    """

    def __init__(self, app: IdfApp, image_path: str):
        """
        Args:
            app: `IdfApp` instance
            image_path: output image path
        """
        self.app = app
        self.image_path = image_path

    def make_bin(self) -> None:
        """
        Create a single image file for qemu.
        """
        if self.app.sdkconfig.get('SECURE_BOOT'):
            self.app.flash_files.append(
                FlashFile(
                    int(self.app.sdkconfig.get('BOOTLOADER_OFFSET_IN_FLASH')),
                    os.path.join(self.app.binary_path, 'bootloader/bootloader.bin'),
                )
            )
        # flash_files is sorted, if the first offset is not 0x0, we need to fill it with empty bin
        if self.app.flash_files[0][0] != 0x0:
            self._write_empty_bin(count=self.app.flash_files[0][0])
        for offset, file_path, encrypted in self.app.flash_files:
            self._write_bin(file_path, seek=offset)

        if self.app.encrypt:
            if self.app.keyfile is None or not os.path.exists(self.app.keyfile):
                raise ValueError('Flash Encryption key file doesn\'t exist')
            self._write_encrypted_bin(self.image_path)

    def _write_empty_bin(self, count: int, bs: int = 1024, seek: int = 0):
        live_print_call(
            f'dd if=/dev/zero bs={bs} count={count} seek={seek} of={self.image_path}',
            shell=True,
        )

    def _write_bin(self, binary_filepath, bs: int = 1, seek: int = 0):
        live_print_call(
            f'dd if={binary_filepath} bs={bs} seek={seek} of={self.image_path} conv=notrunc',
            shell=True,
        )

    def _write_encrypted_bin(self, binary_filepath, bs: int = 1, seek: int = 0):
        live_print_call(
            f'espsecure.py encrypt_flash_data --keyfile {self.app.keyfile} '
            f'--output {self.app.encrypted_image_path} --address {seek} {binary_filepath}',
            shell=True,
        )

    def _burn_efuse(self):
        pass


class QemuApp(IdfApp):
    """
    QEMU App class

    Attributes:
        image_path (str): QEMU flash-able bin path
    """

    def __init__(
        self,
        msg_queue: MessageQueue,
        qemu_image_path: Optional[str] = None,
        skip_regenerate_image: Optional[bool] = False,
        encrypt: Optional[bool] = False,
        keyfile: Optional[str] = None,
        **kwargs,
    ):
        self._q = msg_queue

        super().__init__(**kwargs)

        self.image_path = qemu_image_path or os.path.join(self.binary_path, DEFAULT_IMAGE_FN)
        self.skip_regenerate_image = skip_regenerate_image
        self.encrypt = encrypt
        self.keyfile = keyfile

        if self.encrypt:
            self.encrypted_image_path = os.path.join(self.binary_path, ENCRYPTED_IMAGE_FN)

        if self.target != 'esp32':
            raise ValueError('For now on QEMU we only support ESP32')

        self.create_image()

    def create_image(self) -> None:
        """
        Create the image, if it doesn't exist.
        """
        if os.path.exists(self.image_path) and self.skip_regenerate_image:
            logging.info(f'Using existing image: {self.image_path}')
        else:
            with contextlib.redirect_stdout(self._q):
                image_maker = IdfFlashImageMaker(self, self.image_path)
                image_maker.make_bin()
