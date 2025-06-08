$(document).ready(function () {
    const config = JSON.parse(document.getElementById('config').textContent);
    console.log(config)

    function getTime(offset) {
        const timestamp = config['start_timestamp'] + (offset * config['seconds_per_pixel'])
        //console.log('Time offset', offset, timestamp)
        return new Date(timestamp * 1000)
    }

    function getCamera(event) {
        return event.target.id.replace('timeline-', '')
    }

    function videoURL(videoSrc) {
        var video = document.getElementById('video');
        if (Hls.isSupported()) {
            var hls = new Hls();
            hls.loadSource(videoSrc);
            hls.attachMedia(video);
        }
            // HLS.js is not supported on platforms that do not have Media Source
            // Extensions (MSE) enabled.
            //
            // When the browser has built-in HLS support (check using `canPlayType`),
            // we can provide an HLS manifest (i.e. .m3u8 URL) directly to the video
            // element through the `src` property. This is using the built-in support
        // of the plain video element, without using HLS.js.
        else if (video.canPlayType('application/vnd.apple.mpegurl')) {
            video.src = videoSrc;
        }
    }

    $(".timeline").on("mousemove", function (e) {
        var parentOffset = $(this).parent().offset();
        //or $(this).offset(); if you really just want the current element's offset
        var relX = e.pageX - parentOffset.left;
        var relY = e.pageY - parentOffset.top;
        const time = getTime(relX)
        const camera = getCamera(e);
        //console.log(camera, relX, relY, time)
        $(this).attr("title", camera + " " + time.toLocaleTimeString())
    }).on("mousedown", function (e) {
        var parentOffset = $(this).parent().offset();
        const camera = getCamera(e);
        var relX = e.pageX - parentOffset.left;
        const time = getTime(relX).toISOString()
        const time_obj = getTime(relX)
        $("#video_text").text("Loading recording " + time_obj.toLocaleString())

        console.log('Show recording', camera, time_obj.toLocaleString())
        $.get(`/recording/${camera}/${time}`, function (recording) {
            console.log(recording)
            console.log(window.location)
            $("#video_text").text(`${camera} ${time_obj.toLocaleString()}`)
            //$("#video").src = recording['m3u8_url']
            //const video = document.getElementById('video');
            //video.src = recording['m3u8_url']
            videoURL(recording['m3u8_url'])
            const url = new URL(window.location.origin + "/stream");
            //url.searchParams.set('file', recording.file)
            url.searchParams.set('recording', recording['id'])
            //window.open(url.toString())
        })
    });
});