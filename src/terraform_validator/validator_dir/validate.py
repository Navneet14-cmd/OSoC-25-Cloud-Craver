import subprocess

def validate_directory(path):
    try:
        # Terraform init is required before validate
        subprocess.run(["terraform", "init", "-input=false", "-no-color"], cwd=path, check=True, capture_output=True)

        result = subprocess.run(["terraform", "validate", "-no-color"], cwd=path, check=True, capture_output=True)
        return True  # No error
    except subprocess.CalledProcessError as e:
        print("Terraform validation error:")
        print(e.stderr.decode())
        return False
