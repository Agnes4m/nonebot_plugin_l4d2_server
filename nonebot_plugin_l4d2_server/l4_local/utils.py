def sort_key(filename: str):
    # 提取文件名开头的数字（如果有）
    num_part = ""
    for char in filename:
        if char.isdigit():
            num_part += char
        elif num_part:  # 遇到非数字且已经有数字部分时停止
            break

    # 返回一个元组作为排序依据：(数字值, 整个文件名)
    # 使用正数表示升序，没有数字的用无穷大排在最后
    return (
        int(num_part) if num_part else float("inf"),
        filename,
    )
