import os
import shutil

def remove_pycache_and_pyc(start_path):
    """
    Removes all __pycache__ directories and .pyc files recursively
    from the specified starting path.
    """
    for root, dirs, files in os.walk(start_path):
        # Remove __pycache__ directories
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            print(f"Removing directory: {pycache_path}")
            try:
                shutil.rmtree(pycache_path)
            except OSError as e:
                print(f"Error removing {pycache_path}: {e}")

        # Remove .pyc files
        for file in files:
            if file.endswith('.pyc'):
                pyc_file_path = os.path.join(root, file)
                print(f"Removing file: {pyc_file_path}")
                try:
                    os.remove(pyc_file_path)
                except OSError as e:
                    print(f"Error removing {pyc_file_path}: {e}")

if __name__ == "__main__":
    current_directory = os.getcwd()
    print(f"Starting cleanup from: {current_directory}")
    remove_pycache_and_pyc(current_directory)
    print("Cleanup complete.")