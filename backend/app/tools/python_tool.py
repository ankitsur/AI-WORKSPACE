import tempfile
import subprocess
import os

async def execute_python(code: str):
    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".py",
            mode="w") as temp_file:
            
            temp_file.write(code)

            result = subprocess.run(
                ["python", temp_file.name],
                capture_output=True,
                text=True,
                timeout=10
            )

            os.remove(temp_file.name)

            if result.returncode != 0:
                return f"Error: {result.stderr}"

            return result.stdout
    except Exception as e:
        return f"Error: {e}"