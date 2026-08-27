from typing import AnyStr

from pytest_embedded.dut import Dut

from .qemu import Qemu


class QemuDut(Dut):
    """
    QEMU dut class

    Attributes:
        target (str): target chip type, taken from the app
    """

    def __init__(
        self,
        qemu: Qemu,
        **kwargs,
    ) -> None:
        self.qemu = qemu

        super().__init__(**kwargs)

        # `IdfDut` exposes this for serial runs, and test fixtures use it to
        # select target specific behavior. `QemuApp` is an `IdfApp`, so the
        # target is known here as well; keep it optional for other app classes.
        self.target: str | None = getattr(self.app, 'target', None)

        self._hard_reset_func = self.qemu._hard_reset

    def write(self, s: AnyStr) -> None:
        self.qemu.write(s)

    def hard_reset(self):
        self._hard_reset_func()
