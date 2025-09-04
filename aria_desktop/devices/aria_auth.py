import subprocess

class AriaAuth:
    @staticmethod
    def check() -> bool:
        """Return True if pairing already exists."""
        try:
            subprocess.run(
                ["aria", "auth", "check"],
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def pair() -> None:
        """Run interactive pairing (blocks until user completes)."""
        try:
            subprocess.run(
                ["aria", "auth", "pair"],
                check=True,
                capture_output=True,
                text=True,   
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Pairing failed: {e.stderr}") from e