from utils.jorf_manager import JORF_MANAGER

if __name__ == "__main__":
    download_dir = "jorf_tar_gz"
    destination_dir = "jorf_xml"

    done = True #JORF_MANAGER.download_tar_gz_files(download_dir)
    
    if done == True:
        JORF_MANAGER.read_tar_gz_files(download_dir, destination_dir)
