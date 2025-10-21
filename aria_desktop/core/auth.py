import subprocess
import logger
from ..utils.logger import logger


class AriaAuth:
    """Handles authentication and pairing with Aria devices."""
    @staticmethod
    def check() -> bool:
        """Return True if pairing already exists."""
        try:
            result = subprocess.run(
                ["aria", "auth", "check"],
                check=True,
                capture_output=True,
                text=True,
            )

            out = result.stdout.lower()  # normalize
            err = result.stderr.lower()

            # DEBUG prints
            # logger.debug("aria auth check stdout: %s", out)
            # logger.debug("aria auth check stderr: %s", err)

            # Look for error keywords in stdout (where CLI prints device errors)
            if "no devices found" in out or "there are no devices connected" in out:
                return False

            # Could also catch "error" in stdout
            if "[error]" in out:
                return False

            # If nothing suspicious, assume paired
            logger.info("Device paired to %s", out.strip())
            return result.returncode == 0
        
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def pair() -> None:
        """Run interactive pairing (blocks until user completes)."""
        try:
            result = subprocess.run(
                ["aria", "auth", "pair"],
                check=True,
                # capture_output=True,
                text=True,   
            )

            out = result.stdout.lower()  # normalize
            err = result.stderr.lower()

            # DEBUG prints
            logger.debug("aria auth pair stdout: %s", out)
            logger.debug("aria auth pair stderr: %s", err)
            if result.returncode != 0 or "[error]" in out or "error" in out:
                raise RuntimeError(f"Pairing failed: {out}\n{err}")
            
            logger.info("Sending pairing request, check Companion app and accept the request.")

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Pairing failed: {e.stderr}") from e