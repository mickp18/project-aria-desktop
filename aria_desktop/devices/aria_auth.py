import subprocess

class AriaAuth:
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
            # print("DEBUG: aria auth check stdout:", out)
            # print("DEBUG: aria auth check stderr:", err)

            # Look for error keywords in stdout (where CLI prints device errors)
            if "no devices found" in out or "there are no devices connected" in out:
                return False

            # Could also catch "error" in stdout
            if "[error]" in out:
                return False

            # If nothing suspicious, assume paired
            print("device paired to " + out.strip())
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
                capture_output=True,
                text=True,   
            )

            out = result.stdout.lower()  # normalize
            err = result.stderr.lower()

            # DEBUG prints
            print("DEBUG: aria auth pair stdout:", out)
            print("DEBUG: aria auth pair stderr:", err)
            if result.returncode != 0 or "[error]" in out or "error" in out:
                raise RuntimeError(f"Pairing failed: {out}\n{err}")
            
            print("Sending pairing request, check Companion app and accept the request.")

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Pairing failed: {e.stderr}") from e