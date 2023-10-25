import get_video_sizes
import load_network_trace
import env

"""
测试视频源trace处理功能
"""


def test_get_video_sizes():
    get_video_sizes.get_video_size()


"""
测试网络trace加载功能
"""


def test_load_network_trace():
    all_cooked_time, all_cooked_bw, all_file_names = load_network_trace.load_trace()
    print(all_file_names)


"""
测试播放器在给定网络条件下 下载&播放 一个视频块的模拟功能
"""


def test_video_streaming_env():
    all_cooked_time, all_cooked_bw, all_file_names = load_network_trace.load_trace()
    video_env = env.Environment(all_cooked_time, all_cooked_bw)
    delay, sleep_time, buffer_size, rebuf, video_chunk_size, next_video_chunk_sizes, end_of_video, video_chunk_remain = video_env.get_video_chunk(
        2)
    print(delay)
    print(sleep_time)
    print(buffer_size)
    print(rebuf)
    print(video_chunk_size)
    print(next_video_chunk_sizes)
    print(end_of_video)
    print(video_chunk_remain)


if __name__ == '__main__':
    # test_get_video_sizes()

    # test_load_network_trace()

    test_video_streaming_env()
