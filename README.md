Visual Studio Code

    Microsoft
     - Japanese Language Pack for Visual Studio Code
     - C/C++
     - C/C++ Themes
     - Python
     - Python Debugger
     - Pylance
     - Remote - SSH
     - Remote - SSH: Editing Configuration Files
     - Remote Explorer
    GitHub
     - GitHub Theme
    Other
     - indent-rainbow
     - Rainbow CSV

#include <sys/socket.h>
#include <sys/ioctl.h>
#include <iostream>
#include <unistd.h>

// ソケットバッファのステータスを取得する関数
void checkBufferOverflow(int sockfd) {
    int recv_buf_size;
    socklen_t optlen = sizeof(recv_buf_size);

    // 受信バッファサイズを取得
    if (getsockopt(sockfd, SOL_SOCKET, SO_RCVBUF, &recv_buf_size, &optlen) == -1) {
        perror("getsockopt failed");
        return;
    }

    // 受信バッファ内の未処理データ量を取得
    int bytes_available;
    if (ioctl(sockfd, FIONREAD, &bytes_available) == -1) {
        perror("ioctl failed");
        return;
    }

    // バッファ使用率を計算
    float usage_ratio = static_cast<float>(bytes_available) / recv_buf_size;

    // デバッグ用に現在のバッファ使用率を表示
    std::cout << "Buffer usage: " << usage_ratio * 100 << "% (" 
              << bytes_available << " / " << recv_buf_size << " bytes)" << std::endl;

    // 使用率が80%以上になった場合に警告を出す
    if (usage_ratio > 0.8) {
        std::cerr << "Warning: Receive buffer is getting full! (" 
                  << usage_ratio * 100 << "% used)" << std::endl;
    }

    // 使用率が100%を超えた場合にエラーを出す
    if (usage_ratio >= 1.0) {
        std::cerr << "Error: Buffer overflow imminent! Dropping packets or sending RST." << std::endl;
    }
}

int main() {
    int sockfd = /* あなたのソケットファイルディスクリプタ */;
    
    while (true) {
        // バッファのオーバーフローチェック
        checkBufferOverflow(sockfd);

        // データの受信処理
        char buffer[1024];
        ssize_t bytes_received = recv(sockfd, buffer, sizeof(buffer), 0);
        
        if (bytes_received == -1) {
            perror("recv failed");
            break;
        } else if (bytes_received == 0) {
            // クライアントが接続を閉じた
            std::cout << "Client closed connection" << std::endl;
            break;
        }

        // 受信したデータを処理
        std::cout << "Received " << bytes_received << " bytes" << std::endl;
    }

    close(sockfd);
    return 0;
}