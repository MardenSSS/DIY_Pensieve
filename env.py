import numpy as np

# 随机数生成器的种子
RANDOM_SEED = 42
# 码率阶梯总数
BITRATE_LEVELS = 6
# 视频trace文件名模板
VIDEO_SIZE_FILE = './video_trace/video_size_'
# 单位转换：Mb--->b
B_IN_MB = 1000000.0
# 单位转换：s--->ms
MILLISECONDS_IN_SECOND = 1000.0
# 单位转换：b--->B
BITS_IN_BYTE = 8.0
# 数据包有效载荷，模拟数据包实际承载信息量
PACKET_PAYLOAD_PORTION = 0.95
# 链路RTT
LINK_RTT = 80
# 随机噪声下界
NOISE_LOW = 0.9
# 随机噪声上界
NOISE_HIGH = 1.1
# 视频块时长，in ms
VIDEO_CHUNK_LEN = 4000.0
# 播放器buffer最大长度，in ms
BUFFER_THRESH = 60.0 * MILLISECONDS_IN_SECOND
# 播放器暂停时间粒度，in ms
DRAIN_BUFFER_SLEEP_TIME = 500.0
# todo: 视频块总数为 49，为什么这里设置为 48？？？
# 视频块总数
TOTAL_VIDEO_CHUNK = 48


class Environment:
    """
    format of trace file:
    ---------------------
    time    throughput
    12.151	2.45994005994
    13.161	2.03076435644
    14.181	2.24690196078
    15.182	2.38340859141
    ......
    ----------------------
    """

    def __init__(self, all_cooked_time, all_cooked_bw, random_seed=RANDOM_SEED):
        # 检查 all_cooked_time 和 all_cooked_bw 长度是否相同，若不同则抛出异常
        assert len(all_cooked_time) == len(all_cooked_bw)
        # 设置随机数生成器的种子，确保实验的可重复性
        np.random.seed(random_seed)
        # 初始化 all_cooked_time 变量，所有trace文件的时刻信息
        self.all_cooked_time = all_cooked_time
        # 初始化 all_cooked_bw 变量，所有trace文件的吞吐量信息
        self.all_cooked_bw = all_cooked_bw
        # 初始化 video_chunk_counter 变量，视频块计数
        self.video_chunk_counter = 0
        # 初始化 buffer_size 变量，缓冲区大小
        self.buffer_size = 0

        # 随机选择一个trace文件
        self.trace_idx = np.random.randint(len(self.all_cooked_time))
        self.cooked_time = self.all_cooked_time[self.trace_idx]
        self.cooked_bw = self.all_cooked_bw[self.trace_idx]

        # 随机选择trace文件的起点
        self.mahimahi_ptr = np.random.randint(1, len(self.cooked_bw))
        self.last_mahimahi_time = self.cooked_time[self.mahimahi_ptr - 1]

        self.video_size = {}
        for bitrate in range(BITRATE_LEVELS):
            self.video_size[bitrate] = []
            with open(VIDEO_SIZE_FILE + str(bitrate)) as f:
                for line in f:
                    self.video_size[bitrate].append(int(line.split()[0]))

    """
    模拟：视频播放器在给定网络条件下 下载 &播放 一个视频块的过程
    """

    def get_video_chunk(self, quality):
        # 检查视频块码率取值是否合理，否则抛出异常
        assert quality >= 0
        assert quality < BITRATE_LEVELS

        # 获取要下载的视频块的大小
        video_chunk_size = self.video_size[quality][self.video_chunk_counter]
        # 初始化下载视频块所需的时间，in s
        delay = 0.0
        # 初始化已经下载的视频块大小，in bytes
        video_chunk_counter_sent = 0

        # 模拟一个视频块的下载过程
        while True:
            # 计算当前网络带宽，in bytes
            # 原带宽trace中单位Mb/s
            throughput = self.cooked_bw[self.mahimahi_ptr] * B_IN_MB / BITS_IN_BYTE
            # 计算当前带宽持续时间，in s
            duration = self.cooked_time[self.mahimahi_ptr] - self.last_mahimahi_time
            # 计算当前时间段可以发送的数据量
            packet_payload = throughput * duration * PACKET_PAYLOAD_PORTION
            # 判断当前时间段是否可以将视频块下载完成
            # 若当前时间段可以将视频块下载完成
            if video_chunk_counter_sent + packet_payload > video_chunk_size:
                # 计算下载视频块剩余数据量需要的时间
                fractional_time = (video_chunk_size - video_chunk_counter_sent) / throughput / PACKET_PAYLOAD_PORTION
                # 计算下载视频块所需的时间
                delay += fractional_time
                # 更新trace文件起点，下次下载使用新的起点
                self.last_mahimahi_time += fractional_time
                assert (self.last_mahimahi_time <= self.cooked_time[self.mahimahi_ptr])
                break
            # 若当前时间段不可以将视频块下载完成
            # 更新已经下载的视频块大小
            video_chunk_counter_sent += packet_payload
            # 更新下载视频块所需的时间
            delay += duration
            # 更新网络trace指针，向前推进一个时刻
            self.last_mahimahi_time = self.cooked_time[self.mahimahi_ptr]
            self.mahimahi_ptr += 1

            # 判断是否已经跑完当前的网络trace，从头开始继续循环当前网络trace
            if self.mahimahi_ptr >= len(self.cooked_bw):
                self.mahimahi_ptr = 1
                self.last_mahimahi_time = 0

        # 视频块下载时间转换为ms
        delay *= MILLISECONDS_IN_SECOND
        # 视频块下载时间中添加链路RTT
        delay += LINK_RTT
        # 视频块下载时间添加乘法噪声
        delay *= np.random.uniform(NOISE_LOW, NOISE_HIGH)

        # 计算当前视频块下载产生的rebuffer时间
        rebuf = np.maximum(delay - self.buffer_size, 0.0)
        # 更新当前视频块下载完成后的buffer长度
        self.buffer_size += VIDEO_CHUNK_LEN

        # 初始化播放器暂停下载的时长
        sleep_time = 0
        # 检查当前buffer长度是否超过最大阈值
        # 若当前buffer长度超过最大阈值
        if self.buffer_size > BUFFER_THRESH:
            # 计算当前buffer超过最大阈值的长度
            drain_buffer_time = self.buffer_size - BUFFER_THRESH
            # 计算播放器需要暂停的时长
            sleep_time = np.ceil(drain_buffer_time / DRAIN_BUFFER_SLEEP_TIME) * DRAIN_BUFFER_SLEEP_TIME
            # 更新buffer长度
            self.buffer_size -= sleep_time
            # 模拟播放器暂停下载，网络trace向前推进的过程
            while True:
                # 计算网络trace当前带宽的持续时长
                duration = self.cooked_time[self.mahimahi_ptr] - self.last_mahimahi_time
                # 判断网络trace当前带宽的持续时长是否满足播放器暂停时长
                # 若网络trace当前带宽的持续时长满足播放器暂停时长
                if duration > sleep_time / MILLISECONDS_IN_SECOND:
                    # 更新网络trace指针，向前推进到下一个时刻，及播放器暂停结束的时刻
                    self.last_mahimahi_time += sleep_time / MILLISECONDS_IN_SECOND
                    break
                # 更新播放器暂停时间
                sleep_time -= duration * MILLISECONDS_IN_SECOND
                # 更新网络trace指针，向前推进一个时刻
                self.last_mahimahi_time = self.cooked_time[self.mahimahi_ptr]
                self.mahimahi_ptr += 1
                # 判断是否已经跑完当前的网络trace，从头开始继续循环当前网络trace
                if self.mahimahi_ptr >= len(self.cooked_bw):
                    self.mahimahi_ptr = 1
                    self.last_mahimahi_time = 0

        # 初始化变量，保存当前buffer大小
        return_buffer_size = self.buffer_size
        # 更新当前视频块计数
        self.video_chunk_counter += 1
        # 计算剩余未下载视频块数量
        video_chunk_remain = TOTAL_VIDEO_CHUNK - self.video_chunk_counter
        # 初始化变量，表示是否所有视频块已经下载完成
        end_of_video = False
        # 判断所有视频块是否已经下载完成
        # 若所有视频块下载完成
        if self.video_chunk_counter >= TOTAL_VIDEO_CHUNK:
            # 设置所有视频块下载完成标志，并初始化各项指标
            end_of_video = True
            self.buffer_size = 0
            self.video_chunk_counter = 0
            self.trace_idx = np.random.randint(len(self.all_cooked_time))
            self.cooked_time = self.all_cooked_time[self.trace_idx]
            self.cooked_bw = self.all_cooked_bw[self.trace_idx]
            self.mahimahi_ptr = np.random.randint(1, len(self.cooked_bw))
            self.last_mahimahi_time = self.cooked_time[self.mahimahi_ptr - 1]
        # 若所有视频块下载未完成
        # 收集下一个视频块对应各码率的大小
        next_video_chunk_sizes = []
        for i in range(BITRATE_LEVELS):
            next_video_chunk_sizes.append(self.video_size[i][self.video_chunk_counter])
        # 返回值：
        # 1. 下载总时长
        # 2. 播放器暂停时长
        # 3. 当前buffer大小
        # 4. rebuffer时长
        # 5. 当前下载视频块大小
        # 6. 下一个视频块对应各码率的大小
        # 7. 所有视频块是否下载完成标志
        # 8. 剩余剩余未下载视频块数量
        return (delay,
                sleep_time,
                return_buffer_size / MILLISECONDS_IN_SECOND,
                rebuf / MILLISECONDS_IN_SECOND,
                video_chunk_size,
                next_video_chunk_sizes,
                end_of_video,
                video_chunk_remain
                )
