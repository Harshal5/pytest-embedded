import logging
import typing as t

if t.TYPE_CHECKING:
    from .espemu import EspEmu


class EspEmuSerial:
    """
    The device-state half of an emulated dut.

    ESP-IDF tests reach the chip through two channels: the console stream
    (``dut.expect``) and a control channel (``dut.serial``) that resets it,
    erases flash and burns eFuses. The second one is esptool-backed on
    hardware, and an emulator has no serial port behind it, so the operations
    that are expressible go over esp-emu's control channel instead.

    Only ``hard_reset`` is implemented so far. The rest of ``IdfSerial`` needs
    the emulator in download mode with its UART on a socket, so esptool can
    drive it; until then those methods raise, and the test reports what it
    needed rather than an ``AttributeError`` on a missing attribute.
    """

    def __init__(self, espemu: 'EspEmu') -> None:
        self.espemu = espemu

    @property
    def port(self) -> str:
        """The control channel's address, in the place a port name would be."""
        if self.espemu.control_port is None:
            return 'espemu'
        return f'espemu://127.0.0.1:{self.espemu.control_port}'

    def hard_reset(self) -> None:
        """Reset the chip, the way a DTR/RTS toggle does on hardware."""
        logging.debug('hard resetting the emulated chip')
        self.espemu._hard_reset()

    def close(self) -> None:
        """Nothing to close: the control channel is opened per command."""

    def __getattr__(self, name: str) -> t.Any:
        raise NotImplementedError(
            f'esp-emu cannot do dut.serial.{name}() yet. Only hard_reset is '
            f'implemented; flash and eFuse operations need the emulator in '
            f'download mode with its UART on a socket.'
        )
