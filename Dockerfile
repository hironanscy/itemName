FROM openjdk:11.0.9.1-jdk

LABEL maintainer="nagaisi2@jp.ibm.com"
LABEL description="image to translate japanese item name into english \
      using java and python program, and mecab."

SHELL ["/bin/bash", "-c"]

EXPOSE 8080

ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:jp
ENV LC_ALL ja_JP.UTF-8
ENV PATH $PATH:/usr/bin/

#python, mecab, and etc.
RUN apt -y update && apt install -y \
    python3.7 \
    python3-distutils \
    sudo \
    mecab \
    libmecab-dev \
    mecab-ipadic-utf8 \
    git \
    make \
    curl \
    xz-utils \
    file \
    patch \
    swig \
    locales \
    vim \
    && echo 'alias python3=python3.7' >> ~/.bashrc \
    && source ~/.bashrc \
    && curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
    && sudo python3 get-pip.py \
    && locale-gen ja_JP.UTF-8 \
    && localedef -f UTF-8 -i ja_JP ja_JP \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# python libraries
RUN pip install numpy pandas xlrd mecab-python3 pykakasi

# install mecab-ipadic-neologd
RUN git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git \
    && cd mecab-ipadic-neologd \
    && bin/install-mecab-ipadic-neologd -n -y \
    && mv /usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd /usr/share/mecab/dic \
    && cd .. \
    && rm -rf mecab-ipadic-neologd

# copy custom dictionary file and search program
WORKDIR /itemName
COPY itemName/ .

# copy settings of mecab-dictionary reference
RUN mv ./mecabrc ../etc/mecabrc \
    && sudo cp /etc/mecabrc /usr/local/etc/