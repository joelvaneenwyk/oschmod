#!/bin/sh

if [ ! -e ~/.pyenv ]; then
    curl https://pyenv.run | bash
fi
