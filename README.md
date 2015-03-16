# Director

Entertainment directed by you.

## Introduction

*Director* is a web frontend for your favoured TV shows. All information is
gathered from [XBMC](https://github.com/xbmc/xbmc) nfo and media files.

## Installation

Install package and scripts.

  $ pip install https://github.com/tschaefer/director/archive/master.zip

## Usage

Import your TV shows and episodes.

  $ director -d sqlite:////mnt/storage/media/video/series/director.db import -v /mnt/storage/media/video/series

Start the web service.

  $ director -d sqlite:////mnt/storage/media/video/series/director.db service -H 0.0.0.0 -p 8888 /mnt/storage/media/video/series
