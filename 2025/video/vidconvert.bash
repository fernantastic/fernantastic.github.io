ffmpeg -i ddwc.mp4 -b:v 1000k -vcodec libx264 -preset slow -profile:v baseline -max_muxing_queue_size 1024 -g 30 -s 640x360 ddwc.mp4_web.mp4
ffmpeg -i ddwc.mp4 -b:v 1500k -vcodec libvpx -acodec libvorbis -ab 160000 -f webm    -max_muxing_queue_size 1024 -g 30 -s 640x360 ddwc.mp4_web.webm
ffmpeg -i ddwc.mp4 -b:v 1500k -vcodec libtheora -acodec libvorbis -ab 160000            -max_muxing_queue_size 1024 -g 30 -s 640x360 ddwc.mp4_web.ogv
ffmpeg -i ddwc.mp4 -ss 00:10 -vframes 1 -r 1 -s 640x360 -f image2 ddwc.mp4.jpg