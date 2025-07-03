
def generate_cost_report(output_path):
    print(f"Generating cost report at: {output_path}")

    try:
        with open(output_path, 'w') as f:
            f.write("Cost Report (Stub)\nGenerated from current estimates.")
        print("Report successfully written.")
    except Exception as e:
        print(f"Failed to write report: {e}")
