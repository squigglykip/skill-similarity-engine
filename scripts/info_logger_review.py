import os

def find_info_logger_statements(root_dir):
    """
    Recursively search for 'info.logger' statements in all .py files
    within the specified root directory.

    Args:
        root_dir (str): The path to the root directory to scan.

    Returns:
        dict: A dictionary where keys are file paths and values are
              lists of lines containing 'info.logger'.
    """
    logger_occurrences = {}

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.py'):
                full_path = os.path.join(dirpath, filename)
                try:
                    with open(full_path, 'r', encoding='utf-8') as file:
                        lines = file.readlines()
                        matched_lines = [
                            f"{i+1}: {line.strip()}"
                            for i, line in enumerate(lines)
                            if 'info.logger' in line
                        ]
                        if matched_lines:
                            logger_occurrences[full_path] = matched_lines
                except (UnicodeDecodeError, IOError) as e:
                    print(f"Could not read {full_path}: {e}")

    return logger_occurrences

if __name__ == "__main__":
    directory = input("Enter the path to your codebase: ").strip()
    results = find_info_logger_statements(directory)

    if results:
        print("\nFound 'info.logger' in the following files:\n")
        for file, lines in results.items():
            print(f"\n{file}")
            for line in lines:
                print(f"  {line}")
    else:
        print("\nNo 'info.logger' statements found.")
