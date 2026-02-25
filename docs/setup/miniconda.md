# Miniconda 安装 & 环境管理

> 官方文档: https://docs.conda.io/projects/conda/en/stable/

## 安装

### macOS (Apple Silicon)

```bash
# 下载安装包
curl -fsSLO https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh

# 安装（-b 静默模式，-p 指定路径）
bash Miniconda3-latest-MacOSX-arm64.sh -b -p $HOME/miniconda3

# 初始化 shell（zsh）
~/miniconda3/bin/conda init zsh
source ~/.zshrc

# 验证
conda --version
```

### macOS (Intel)

```bash
curl -fsSLO https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
bash Miniconda3-latest-MacOSX-x86_64.sh -b -p $HOME/miniconda3
```

### Linux

```bash
curl -fsSLO https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
~/miniconda3/bin/conda init bash
source ~/.bashrc
```

---

## 环境管理速查

### 创建 & 删除

```bash
# 创建环境（指定 Python 版本）
conda create -n avicenna python=3.10 -y

# 从 requirements.txt 创建
conda create -n avicenna python=3.10 -y && conda activate avicenna && pip install -r requirements.txt

# 克隆已有环境
conda create -n avicenna-dev --clone avicenna

# 删除环境
conda remove -n avicenna --all -y
```

### 激活 & 切换

```bash
conda activate avicenna       # 激活
conda deactivate               # 退出到 base
conda activate base            # 回到 base
```

### 查看信息

```bash
conda env list                 # 列出所有环境
conda list                     # 当前环境的包列表
conda list | grep mineru       # 搜索特定包
conda info                     # conda 自身信息
```

### 安装包

```bash
# conda 安装
conda install numpy pandas -y

# pip 安装（在 conda 环境内）
pip install mineru>=2.7

# 从 requirements.txt
pip install -r requirements.txt

# 以开发模式安装当前项目
pip install -e .
```

### 导出 & 复现

```bash
# 导出环境（完整，跨平台性差）
conda env export > environment.yml

# 导出仅手动安装的包（推荐）
conda env export --from-history > environment.yml

# 从 yml 复现
conda env create -f environment.yml
```

---

## 常用配置

```bash
# 关闭自动激活 base 环境
conda config --set auto_activate_base false

# 加速：使用 libmamba solver（conda >= 22.11）
conda config --set solver libmamba

# 添加清华源（国内加速）
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --set show_channel_urls yes
```

---

## 项目环境配置

```bash
# avicenna 推荐环境
conda create -n avicenna python=3.10 -y
conda activate avicenna
pip install -e .                # 安装 avicenna 及所有依赖

# 如需 GPU 后端（vlm-transformers）
conda install pytorch torchvision pytorch-cuda=12.1 -c pytorch -c nvidia -y
```
