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

    // Reading the raw UTF-8 bytes directly from Python
    while(std::getline(std::cin, video_file_name)) {
        std::cout << video_file_name << std::endl;

        fs::path filename_path{ video_file_name };
        fs::path video_file_path{videos_folder_path / filename_path};

        if (!fs::exists(video_file_path)) {
            std::cerr << "Video file not found: " << video_file_path.string() << std::endl;
            return 2;
        }

        std::cout << "Generating command" << std::endl;

        std::string command {
            std::string("ffmpeg -ss 00:00:05 -i ") +
            "\"" + video_file_path.string() + "\"" +
            R"( -vf "select='eq(pict_type,I)'" -vframes 1 -q:v 2 )" +
            "\"" + (output_folder_path / video_file_path.filename()).string() + ".jpg" + "\""
        };
        std::cout << command << "\n" << std::endl;

        std::system(command.c_str());
    }

    return 0;
}