import os

TOTAL_VIDEO_CHUNCK = 49
BITRATE_LEVELS = 6
VIDEO_PATH = './video_trace/'
VIDEO_FOLDER = 'video'

""""
读取指定路径的视频trace，获取视频大小信息并保存到指定路径
    w：文本写入模式
    wb：二进制写入模式
"""


def get_video_size():
    for bitrate in range(BITRATE_LEVELS):
        with open(VIDEO_PATH + 'video_size_' + str(bitrate), 'w') as f:
            for chunk_num in range(1, TOTAL_VIDEO_CHUNCK + 1):
                video_chunk_path = VIDEO_PATH + \
                                   VIDEO_FOLDER + \
                                   str(BITRATE_LEVELS - bitrate) + \
                                   '/' + \
                                   str(chunk_num) + \
                                   '.m4s'
                chunk_size = os.path.getsize(video_chunk_path)
                f.write(str(chunk_size) + '\n')