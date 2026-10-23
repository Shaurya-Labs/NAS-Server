#include <iostream>
#include <cstdlib>
#include <string>
#include <filesystem>

namespace fs = std::filesystem;

int main(int argc, char* argv[]) {

    std::setlocale(LC_ALL, ".UTF-8");
    if(argc != 3) {
        return 1;
    }

    fs::path videos_folder_path{argv[1]};
    fs::path output_folder_path{argv[2]};
    std::string video_file_name{};

    std::cout << "DEBUG: Videos folder path initialized to: " << videos_folder_path << std::endl;
    std::cout << "DEBUG: Output folder path initialized to: " << output_folder_path << std::endl;

    bool is_error_encountered {false};

    // Reading the raw UTF-8 bytes directly from Python
    while(std::getline(std::cin, video_file_name)) {
        std::cout << "INFO: Generating thumbnail for: " << video_file_name << std::endl;

        fs::path filename_path{ video_file_name };
        fs::path video_file_path{videos_folder_path / filename_path};

        if (!fs::exists(video_file_path)) {
            std::cout << "ERROR: Video file not found: " << video_file_path.string() << std::endl;
            is_error_encountered = true;
        }

        std::cout << "DEBUG: Generating command" << std::endl;

        std::string command {
                std::string("ffmpeg -ss 00:00:05 -i ") +
                "\"" + video_file_path.string() + "\"" +
                R"( -vf "select='eq(pict_type,I)'" -vframes 1 -update 1 -strict -2 -q:v 2 )" +
                "\"" + (output_folder_path / video_file_path.filename()).string() + ".jpg" + "\""   
            };

        std::cout << "DEBUG: Command generated successfully: " << command << std::endl;

        int result { std::system(command.c_str()) };
        
        if (result != 0) {
            std::cout << "ERROR: Encountered an error while generating thumbnail for: " << video_file_name << std::endl;
            is_error_encountered = true;
        }
    }
    return is_error_encountered ? 1 : 0; // return 1 if an error was encountered, otherwise return 0
}