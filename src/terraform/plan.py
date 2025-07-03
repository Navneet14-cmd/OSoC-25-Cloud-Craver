import subprocess
import os

def generate_terraform_plan_json(directory: str = ".", out_file: str = "plan.out"):
    print("Initializing Terraform and generating Terraform binary plan...")
    binary_plan = "tfplan.binary"

    try:
        subprocess.run(["terraform", "init", "-input=false"], cwd=directory, check=True)
        print("Terraform initialization complete.")

        subprocess.run(["terraform", "plan", f"-out={binary_plan}"], cwd=directory, check=True)
        print("Binary plan generated.")

        with open(os.path.join(directory, out_file), "w") as f:
            subprocess.run(["terraform", "show", "-json", binary_plan], cwd=directory, check=True, stdout=f)
        print(f"Terraform plan JSON written to: {os.path.join(directory, out_file)}")

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Terraform command failed: {e}")
    except Exception as e:
        print(f"[ERROR] Failed to generate plan: {e}")
