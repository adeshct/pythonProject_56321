import os
import shutil

def rename_and_move_files(start_folder='C:/Users/adeshvijaya/pythonProject_56321/deploy/trades')
    

    for foldername, subfolders, filenames in os.walk(start_folder):
        for filename in filenames:
            if filename == 'trades.json':
                new_name = os.path.join(foldername, foldername.split(os.path.sep)[-1] + '-' + filename)
                new_path = "C:/Users/adeshvijaya/pythonProject_56321/deploy/trades/Compiled"
                old_path = os.path.join(foldername, filename)
                os.rename(old_path, new_name)
                shutil.move(new_name, new_path)

if __name__ == "__main__":
    rename_and_move_files()
