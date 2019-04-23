#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Raphael Matto
# https://github.com/raphaelmatto/flickr-archive
# Created March 2019.

from __future__ import division

import os
import re
import math
import json
import time
import logging
import collections
from datetime import datetime

from PIL import Image
from resizeimage import resizeimage

_TWITTER_BOOTSTRAP = '<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">'
_FLICKR_URL = "https://www.flickr.com"


def _set_up_logging(logging_level=logging.DEBUG):
    if not os.path.exists("logs"):
        os.makedirs("logs")
    datestamp = datetime.now().strftime("%Y_%m_%d_%H-%M-%S")
    log = os.path.join(
        "logs",
        "%s_%s.log" % (
            os.path.splitext(os.path.basename(__file__))[0],
            datestamp,
        )
    )
    logging.basicConfig(
        filename=log,
        level=logging_level,
        format="%(levelname)s: %(asctime)s: %(message)s",
    )
    logging.getLogger().addHandler(logging.StreamHandler())
    return log


def _create_dirs():
    """
    Creates file structure, so:
    html
        - images
        - albums
        - thumbnails
        - tags
    cache
    """
    if not os.path.isdir("cache"):
        os.makedirs("cache")
        logging.info("Created cache folder.")

    if not os.path.isdir("html"):
        os.makedirs("html")
        logging.info("Created html folder.")

    if not os.path.isdir("html/images"):
        os.makedirs("html/images")
        logging.info("Created html/images folder.")

    if not os.path.isdir("html/albums"):
        os.makedirs("html/albums")
        logging.info("Created html/albums folder.")

    if not os.path.isdir("thumbnails"):
        os.makedirs("thumbnails")

    if not os.path.isdir("html/tags"):
        os.makedirs("html/tags")
        logging.info("Created html/tags folder.")

    if not os.path.isdir("html/comments"):
        os.makedirs("html/comments")
        logging.info("Created html/comments folder.")

    if not os.path.isdir("html/views"):
        os.makedirs("html/views")
        logging.info("Created html/views folder.")

    if not os.path.isdir("html/favs"):
        os.makedirs("html/favs")
        logging.info("Created html/favs folder.")


def _create_profile_html(image_map):
    json_data = _get_json_data('account_profile.json')
    html = """
        <html>
            <head>
                <title>
                </title>
                {twitter_bootstrap}
                <style>
                    {style}
                </style>
            </head>
            <body>
                <div>
                    <h1>{name}</h1>
                    <hr>
                    <p>
                        Albums: {albums}<br>
                        Tags: {tags}<br>
                        Favorites: {faves}<br>
                        Comments: {comments}<br>
                        Views: {views}
                    </p>
                    <hr>
                    <h2>Details</h2>
                    City: {city}<br>
                    Hometown: {hometown}
                    <hr>
                    <h2>Profile</h2>
                    <p>
                        {description}
                    </p>
                </div>
            </body>
        </html>
    """.format(
        style="""
            div {padding: 50px 160px 50px 160px;}
            .img {
                width: 300px;
                height: 300px;
                background-position: 50% 50%;
                background-repeat: no-repeat;
                background-size: cover;
            }
        """,
        twitter_bootstrap=_TWITTER_BOOTSTRAP,
        city=json_data["city"],
        hometown=json_data["hometown"],
        name=json_data['real_name'],
        faves="<a href=favs-1.html>%s</a>" % "{:,}".format(int(json_data['stats']['faves_count'])),
        comments="<a href=comments-1.html>%s</a>" % "{:,}".format(int(json_data['stats']['comments_count']['photos'])),
        views="<a href=views-1.html>%s</a>" % "{:,}".format(json_data['stats']['view_counts']['total']),
        description=json_data["description"].replace("\n", "<br>"),
        albums="<a href=albums-1.html>%s</a>" % len(_get_albums()),
        tags="<a href=tags-1.html>%s</a>" % json_data["stats"]["tags_count"],
    )
    _write_html(html, "./html/index.html", overwrite=True)


def _create_thumbnail_images(image_map, overwrite=False):
    for file in image_map.values():
        _, ext = os.path.splitext(file)
        supported_formats = [".jpg", ".jpeg", ".JPG", ".JPEG", ".gif", ".GIF", ".png", ".PNG"]
        if ext not in supported_formats:
            logging.info(
                "%s with extension %s is not a supported format, skipping ..." % (file, ext)
            )
            continue
        logging.info("Creating thumnail image for %s ..." % file)
        if os.path.exists("thumbnails/%s" % file) and not overwrite:
            logging.info("Thumbnail for %s already exists, skipping ..." % file)
            continue
        try:
            with open("images/%s" % file, "r+b") as fh:
                with Image.open(fh) as image:
                    cover = resizeimage.resize_cover(image, [300, 300])
                    cover.save("thumbnails/%s" % file, image.format)
        except Exception as e:
            logging.error(
                "Couldn't create thumbnail for %s: %s" % (file, e.message)
            )


def _get_json_files(type):
    if type == "images":
        return [x for x in os.listdir("json") if "photo_" in x]


def _get_json_data(json_file):
    with open("json/%s" % json_file) as fh:
        return json.load(fh, strict=False, encoding="utf-8")


def _write_html(html, file_path, overwrite=True):
    try:
        if os.path.exists(file_path) and not overwrite:
            logging.info("%s already exists, skipping ..." % file_path)
            return
        logging.info("Writing %s ..." % file_path)
        with open(file_path, "w") as fh:
            fh.write(html)
    except Exception as e:
        logging.error("Could not write %s: %s" % (file_path, e.message))


def _get_people(people):
    if type(people) is list:
        return ", ".join(["<a href={flickr}/photos/{person}>{person}</a>".format(flickr=_FLICKR_URL, person=x["person"]) for x in people])
    return None


def _get_exif(exif):
    if type(exif) is dict:
        for k, v in exif.items():
            return "\n".join(
                ["%s: %s" % (k, json.dumps(v, indent=4)) for k, v in exif.items()]
            )


def _get_tags(tags):
    return "<br>".join(["<a href=../tags/{tag}.html>{tag_clean}</a>".format(tag_clean=x["tag"].encode("utf-8"), tag=x["tag"].encode("utf-8").replace("/", "-",).replace(" ", "-")) for x in tags])


def _get_groups(group):
    return "<br>".join(["<a href={url}>{name}</a>".format(url=x["url"].encode("utf-8"), name=x["name"].encode("utf-8")) for x in group])


def _get_location(geo):
    try:
        return "latitude={latitude}, longitude={longitude}, accuracy={accuracy}".format(
            latitude=geo["latitude"],
            longitude=geo["longitude"],
            accuracy=geo["accuracy"],
        )
    except:
        return ""


def _get_image_albums(albums):
    return "<br>".join(["<a href=../albums/{id}.html>{title}</a>".format(id=x["id"], title=x["title"]) for x in albums])


def _get_privacy(privacy):
    return privacy.encode("utf-8")


def _create_image_map(write=False):
    """
    Creates a map of image ids -> image file paths,
    as in:
    {
        "131099312": "fresh-crop_131099312_o.jpg",
        "133996756": "t-rex-back-to-the-cretacious-3d-imax_133996756_o.jpg",
        ...
    }
    ... and optionaly writes it to disk.
    """
    logging.info("Mapping image ids to images ...")
    images = os.listdir("images")
    map = {}
    regexA = re.compile("^(\d+)_")
    regexB = re.compile("_(\d+)_o")
    regexC = re.compile("_(\d+)\.")
    for image in images:
        found = False
        match = re.search(regexA, image)
        if match:
            found = True
            id = match.group(1)
            map[id] = image
        match = re.search(regexB, image)
        if match:
            found = True
            id = match.group(1)
            map[id] = image
        match = re.search(regexC, image)
        if match:
            found = True
            id = match.group(1)
            map[id] = image
        if not found:
            logging.debug("Can't get id for images/%s, skpping ..." % image)
    if write:
        with open("./cache/map.json", "w") as fh:  
            json.dump(map, fh, indent=4)
    return map


def _niceDate(date_string):
    try:
        dt = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
    except:
        dt = datetime.strptime(date_string, '%Y-%m-%d %H: %M: %S')
    return "%s %s, %s" % (dt.strftime("%B"), dt.day, dt.year)


def _create_image_html(json_data, image_map):
    html = """
        <html>
            <head>
                <title>
                </title>
                {twitter_boostrap}
                <style>
                    {style}
                </style>
            </head>
            <body>
                <div class=padding>
                    <div class="imgbox">
                        <img class="center-fit" src={image_src}>
                    </div>
                    <br>
                    <div align=center>
                        <h1><a href={flickr_link}>{name}</a></h1>
                        <p>{date_taken}</p>
                        <p>{views} views, {favorites} favorites</p>
                    </div>
                    <hr>
                    <h2>Description</h2>
                    <p>{description}</p>
                    <hr>
                    <h2>Comments ({num_comments})</h2>
                    {comments}
                    <hr>
                    <h2>Albums</h2>
                    {albums}
                    <hr>
                    <h2>Tags</h2>
                    {tags}
                    <hr>
                    <h2>Groups</h2>
                    {groups}
                    <hr>
                    <h2>Details</h2>
                    <p>
                        Privacy: {privacy}<br>
                        People in the photo: {people}<br>
                        Location: {location}<br>
                        License: {license}<br>
                    </p>
                    <hr>
                    <h2>Exif</h2>
                    <pre>{exif}</pre>
                </div>
            </body>
        </html>
    """.format(
        style="""
            .padding {
                padding: 0px 160px 50px 160px;
            }
            * {
                margin: 0;
                padding: 0;
            }
            .imgbox {
                display: grid;
                height: 100%;
            }
            .center-fit {
                max-width: 100%;
                max-height: 100vh;
                margin: auto;
            }
        """,
        location=_get_location(json_data.get("geo")),
        albums=_get_image_albums(json_data["albums"]),
        views=json_data["count_views"],
        license=json_data["license"],
        groups=_get_groups(json_data["groups"]),
        tags=_get_tags(json_data["tags"]),
        description=json_data["description"].encode("utf-8"),
        favorites=json_data["count_faves"],
        flickr_link=json_data["photopage"],
        comments=_get_comments_html(json_data["comments"]),
        num_comments=json_data["count_comments"],
        name=json_data["name"].encode("utf-8"),
        twitter_boostrap=_TWITTER_BOOTSTRAP,
        image_src="../../images/%s" % image_map.get(json_data["id"]),
        date_taken=_niceDate(json_data["date_taken"]),
        people=_get_people(json_data["people"]),
        count_comments=json_data["count_comments"],
        rotation=json_data["rotation"],
        date_imported=json_data["date_imported"],
        tagging_permissions=json_data["tagging_permissions"],
        exif=_get_exif(json_data["exif"]),
        privacy=_get_privacy(json_data["privacy"]),
    )
    return html


def _create_images_html(image_map, overwrite=True):
    """
    Creates an html file for each known
    image in the images directory. Also writes
    a tags map and returns it.
    """
    tags = {}
    favs = {}
    views = {}
    comments = {}
    json_files = _get_json_files("images")
    for json_file in json_files:
        # For testing.
        # if "5055428455" not in json_file:
        #     continue
        try:
            json_data = _get_json_data(json_file)
            for tag in json_data["tags"]:
                tags.setdefault(tag["tag"], [])
                tags[tag["tag"]].append(json_data["id"])
            favs.setdefault(json_data["count_faves"], [])
            views.setdefault(json_data["count_views"], [])
            comments.setdefault(json_data["count_comments"], [])
            favs[json_data["count_faves"]].append(json_data["id"])
            views[json_data["count_views"]].append(json_data["id"])
            comments[json_data["count_comments"]].append(json_data["id"])
            html = _create_image_html(json_data, image_map)
            _write_html(
                html,
                "html/images/%s.html" % json_data["id"],
                overwrite=overwrite,
            )
        except Exception as e:
            logging.exception(e)
            exit()

    logging.info("Writing ./cache/tags.json ...")
    with open("./cache/tags.json", "w") as fh:
        json.dump(tags, fh, indent=4)

    logging.info("Writing ./cache/favs.json ...")
    with open("./cache/favs.json", "w") as fh:
        json.dump(favs, fh, indent=4)

    logging.info("Writing ./cache/views.json ...")
    with open("./cache/views.json", "w") as fh:
        json.dump(views, fh, indent=4)

    logging.info("Writing ./cache/comments.json ...")
    with open("./cache/comments.json", "w") as fh:
        json.dump(comments, fh, indent=4)

    return tags, favs, views, comments


def _get_comments_html(comments):
    html = ""
    for comment in comments:
        html += """
            <div style="font-size: 75%"><a href={flickr}/photos/{user}>{user}</a> on {date}</div>
            {comment}<br><br>
        """.format(
            flickr=_FLICKR_URL,
            user=comment["user"],
            date=_niceDate(comment["date"]),
            comment=comment["comment"].encode('utf-8'),
        )
    return html


def _get_images_table(image_ids, image_map):
    table = '<table cellpadding=10 border=0>'
    count = 1
    for image_id in image_ids:
        try:
            if count == 0:
                table += "<tr>"
            table += """
                <td>
                    <a href=../images/{id}.html><img src={url}></a>
                    <a href=../images/{id}.html>{id}</a>
                    <br><br>
                </td>

            """.format(
                url="../../thumbnails/%s" % image_map[image_id],
                id=image_id,
            )
            if count == 4:
                table += "</tr>"
                count = 0
            count += 1
        except Exception as e:
            logging.error(
                "Could not find %s in image map: %s" % (
                    image_id,
                    e.message,
                )
            )
    table += "</table>"
    return table


def _get_albums():
    return sorted(
        _get_json_data("albums.json")["albums"],
        key=lambda k: k['title'],
    )


def _get_album_table(albums, image_map):
    table = '<table cellpadding=10 border=0>'
    count = 1
    for album in albums:
        try:
            cover_photo = image_map[_id_from_url(album["cover_photo"])]
        except Exception as e:
            cover_photo = ""
            logging.error(
                "Could not find %s in image map to use as cover photo for %s: %s" % (
                    _id_from_url(album["cover_photo"]),
                    album["title"],
                    e.message,
                )
            )
        table += """
            {tr}
            <td>
                <a href=./albums/{id}.html><img src={link}></a><br>
                <a href=./albums/{id}.html>{title} ({num_photos})</a><br>
            </td>

        """.format(
            tr="<tr>" if count == 0 else "",
            link="../thumbnails/%s" % cover_photo,
            id=album["id"],
            title=album["title"],
            num_photos=album["photo_count"],
        )
        if count == 4:
            table += "</tr>"
            count = 0
        count += 1

    table += "</table>"
    return table


def _get_tag_table(tags, image_map):
    table = '<table cellpadding=10 border=0>'
    count = 1
    for tag in tags:
        cover_photo = image_map[tag["images"][0]]  # First image in list.
        table += """
            {tr}
            <td>
                <a href=./tags/{tag}.html><img src={link}></a><br>
                <a href=./tags/{tag}.html>{tag_clean} ({num_photos})</a><br>
            </td>

        """.format(
            tr="<tr>" if count == 0 else "",
            link="../thumbnails/%s" % cover_photo,
            tag=tag["name"].encode('utf-8').replace("/", "-").replace(" ", "-"),
            tag_clean=tag["name"].encode('utf-8'),
            num_photos=len(tag["images"]),
        )
        if count == 4:
            table += "</tr>"
            count = 0
        count += 1

    table += "</table>"
    return table


def _get_table(type, types, image_map):
    table = '<table cellpadding=10 border=0>'
    count = 1
    for i in types:
        cover_photo = image_map[i["images"][0]]  # First image in list.
        table += """
            {tr}
            <td>
                <a href=./{type}s/{num}.html><img src={link}></a><br>
                <a href=./{type}s/{num}.html>{num} {type} ({num_photos})</a><br>
            </td>

        """.format(
            type=type,
            tr="<tr>" if count == 0 else "",
            link="../thumbnails/%s" % cover_photo,
            num=i["num"],
            num_photos=len(i["images"]),
        )
        if count == 4:
            table += "</tr>"
            count = 0
        count += 1

    table += "</table>"
    return table


def _create_tag_html(tag, page_num, image_map, overwrite):
    """
    Creates an html page for a tag.
    """
    if len(tag["images"]) > 30:
        images = _get_images_table(tag["images"], image_map)
    else:
        images = "<br><br>".join(["<a href=../images/%s.html><img class='center-fit' src=../../images/%s></a>" % (x, image_map.get(x)) for x in tag["images"]])
    url = ""
    try:
        url="%s/search/?sort=date-taken-desc&safe_search=1&tags=%s&user_id=%s&view_all=1" % (
            _FLICKR_URL,
            tag["name"].encode("utf-8").replace("/", "-").replace(" ", "-"),
            _get_flickr_id(),
        )
    except Exception as e:
        logging.error(
            "Could not create Flickr link for %s: %s" % (
                tag["name"],
                e.message,
            )
        )
    html = """
        <html>
            <head>
                <title>
                </title>
                {twitter_boostrap}
                <style>
                    {style}
                </style>
            </head>
            <body>
                <div class=padding>
                    <h1><a href={url}>{title}</a></h1>
                    <hr>
                    <a href=../index.html>Home</a> / <a href=../tags-{page_num}.html>Tags, page {page_num}</a>
                    <hr>
                    <p>
                        {photo_count} photo{plural}<br><br>
                    </p>
                    <div align=center class='imgbox'>
                        {images}
                    </div>
                </div>
            </body>
        </html>
    """.format(
        style="""
            .padding {
                padding: 50px 160px 50px 160px;
            }
            * {
                margin: 0;
                padding: 0;
            }
            .imgbox {
                display: grid;
                height: 100%;
            }
            .center-fit {
                max-width: 100%;
                max-height: 100vh;
                margin: auto;
            }
        """,
        plural="s" if int(len(tag["images"])) > 1 else "",
        twitter_boostrap=_TWITTER_BOOTSTRAP,
        title=tag["name"].encode("utf-8"),
        page_num=page_num,
        photo_count=len(tag["images"]),
        url=url,
        images=images,
    )
    _write_html(
        html,
        "./html/tags/%s.html" % tag["name"].encode("utf-8").replace("/", "").replace(" ", "-"),
        overwrite=overwrite,
    )


def _create_tags_page(tags, page_num, num_pages, image_map, overwrite):
        html = """
            <html>
                <head>
                    <title>
                    </title>
                    {twitter_boostrap}
                    <style>
                        {style}
                    </style>
                </head>
                <body>
                    <div class=padding>
                        <h1>Tags, page {page_num}</h1>
                        <hr>
                        <a href=index.html>Home</a>
                        <hr>
                        <center>{pages}</center>
                        <hr>
                        {tags}
                        <hr>
                        <center>{pages}</center>
                    </div>
                </body>
            </html>
        """.format(
            page_num=page_num,
            pages="Pages: " + " | ".join(["<a href=tags-%s.html>%s</a>" % (x, x) for x in range(1, num_pages)]),
            style="""
                .padding {
                    padding: 50px 160px 50px 160px;
                }
                * {
                    margin: 0;
                }
                """,
            twitter_boostrap=_TWITTER_BOOTSTRAP,
            tags=_get_tag_table(tags, image_map),
        )
        _write_html(html, "./html/tags-%s.html" % str(page_num), overwrite=overwrite)


def _get_num_tags(tags):
    count = 0
    for num_images, _tags in tags.items():
        count += len(_tags)
    return count


def _create_tags_html(tags, image_map, overwrite=True):
    """
    Parses the tags dict and writes html for tags
    """
    tags_per_page = 200
    cur_page_num = 1
    count = 0
    cur_page_tags = []
    num_pages = int(math.ceil(_get_num_tags(tags) / tags_per_page))
    for num_images, _tags in tags.items():
        for tag in _tags:
            # if not tag["name"] == "kids":
            #     continue
            count += 1
            cur_page_tags.append(tag)
            if count == tags_per_page:
                _create_tags_page(cur_page_tags, cur_page_num, num_pages, image_map, overwrite)
                cur_page_tags = []
                count = 0
                cur_page_num += 1
            _create_tag_html(
                tag,
                cur_page_num,
                image_map,
                overwrite,
            )
    if len(cur_page_tags) > 0:
        _create_tags_page(cur_page_tags, cur_page_num, num_pages, image_map, overwrite)


def _create_album_html(album, page_num, image_map):
    if len(album["photos"]) > 30:
        images = _get_images_table(album["photos"], image_map)
    else:
        images = "<br><br>".join(["<a href=../images/%s.html><img class='center-fit' src=../../images/%s></a>" % (x, image_map.get(x)) for x in album["photos"]])
    html = """
        <html>
            <head>
                <title>
                </title>
                {twitter_boostrap}
                <style>
                    {style}
                </style>
            </head>
            <body>
                <div class=padding>
                    <h1><a href={url}>{title}</a></h1>
                    <hr>
                    <a href=../index.html>Home</a> / <a href=../albums-{page_num}.html>Albums, page {page_num}</a>
                    <hr>
                    <p>
                        {photo_count} photo{plural}<br><br>
                        {description}
                    </p>
                    <div align=center class='imgbox'>
                        {images}
                    </div>
                </div>
            </body>
        </html>
    """.format(
        style="""
            .padding {
                padding: 50px 160px 50px 160px;
            }
            * {
                margin: 0;
                padding: 0;
            }
            .imgbox {
                display: grid;
                height: 100%;
            }
            .center-fit {
                max-width: 100%;
                max-height: 100vh;
                margin: auto;
            }
        """,
        plural="s" if int(album["photo_count"]) > 1 else "",
        date=time.strftime("%A %b %d, %Y", time.gmtime(int(album["last_updated"]))),
        twitter_boostrap=_TWITTER_BOOTSTRAP,
        title=album["title"],
        page_num=page_num,
        photo_count=album["photo_count"],
        description=album["description"].encode('utf-8'),
        url=album["url"],
        images=images,
    )
    return html


def _create_albums_html(image_map, overwrite=True):
    # Write html file(s) to list all albumns
    albums = _get_albums()
    albums_per_page = 100
    num_pages = int(math.ceil(len(albums) / albums_per_page))
    for page_num in range(num_pages):
        albums_on_page = albums[albums_per_page * page_num:albums_per_page * (page_num + 1)]
        html = """
            <html>
                <head>
                    <title>
                    </title>
                    {twitter_boostrap}
                    <style>
                        {style}
                    </style>
                </head>
                <body>
                    <div class=padding>
                        <h1>Albums, page {page_num}</h1>
                        <hr>
                        <a href=index.html>Home</a>
                        <hr>
                        <center>{pages}</center>
                        <hr>
                        {albums}
                        <hr>
                        <center>{pages}</center>
                    </div>
                </body>
            </html>
        """.format(
            page_num=page_num + 1,
            pages="Pages: " + " | ".join(["<a href=albums-%s.html>%s</a>" % (x + 1, x + 1) for x in range(0, num_pages)]),
            style="""
                .padding {
                    padding: 50px 160px 50px 160px;
                }
                * {
                    margin: 0;
                }
                """,
            twitter_boostrap=_TWITTER_BOOTSTRAP,
            albums=_get_album_table(albums_on_page, image_map),
        )
        _write_html(html, "./html/albums-%s.html" % str(page_num + 1), overwrite=overwrite)

        # Write html file(s) for each album
        for album in albums_on_page:
            html = _create_album_html(album, page_num + 1, image_map)
            _write_html(
                html,
                "./html/albums/%s.html" % album["id"],
                overwrite=overwrite,
            )


def _create_albums_symlinks(image_map):
    """
    Creates an album dir for each album in
    albums.json, and creates a symlink to
    each image in the album.
    """
    albums = _get_albums()
    regex = re.compile("(.*)_\d+_o.(\w+)")
    for album in albums:
        dir = "albums/%s" % album["title"]
        if not os.path.isdir(dir):
            logging.info("Creating folder %s ..." % dir)
            os.makedirs(dir)
        for photo in album["photos"]:
            if photo == "0":
                continue
            if photo not in image_map:
                continue
            match = re.search(regex, image_map[photo])
            if match:
                nice_name = "%s.%s" % (match.group(1), match.group(2))
                dst = os.path.abspath("albums/%s/%s" % (album["title"], nice_name))
                if not os.path.lexists(dst):
                    src = os.path.abspath("images/%s" % image_map[photo])
                    logging.info("Linking %s to %s ..." % (src, dst))
                    os.symlink(src, dst)
                else:
                    logging.info("%s already exists, skipping ..." % dst)


def _id_from_url(url):
    return url.split("/")[-1]


def _get_cache():
    """
    Loads up cache files from disk, so we
    don't have to go through the images loop
    while testing.
    """

    with open('./cache/tags.json') as fh:
        tags = json.load(fh)

    with open('./cache/favs.json') as fh:
        favs = json.load(fh)

    with open('./cache/views.json') as fh:
        views = json.load(fh)

    with open('./cache/comments.json') as fh:
        comments = json.load(fh)

    with open('./cache/map.json') as fh:
        image_map = json.load(fh)

    return tags, favs, views, comments, image_map


def _get_flickr_id():
    return _get_json_data('account_profile.json')["nsid"]


def _sort_by_value_len(_dict):
    """
    to_sort: a dict with structure:
    {
        {'key1': ['value1', 'value2']},
        {'key2': ['value1', 'value2']},
    }
    """
    to_sort = {}
    for k, v in _dict.items():
        if len(v) not in to_sort:
            to_sort[len(v)] = [{"name": k, "images": v}]
        else:
            to_sort[len(v)].append({"name": k, "images": v})
    sorted_dict = collections.OrderedDict()
    for k, v in sorted(to_sort.iteritems(), reverse=True):
        sorted_dict[k] = v
    return sorted_dict


def _combine_tags(tags):
    """
    Since url addresses do not respect case, we
    convert all tags to lowercase, and combine tags
    with the same chars. For example, Kids: [1, 2]
    and kids: [3, 4] becomes kids: [1, 2, 3, 4].
    """
    clean_tags = {}
    for tag, images in tags.items():
        tag = tag.lower()
        if tag not in clean_tags:
            clean_tags[tag] = list(images)
        else:
            clean_tags[tag].extend(list(images))
            clean_tags[tag] = set(clean_tags[tag])
            clean_tags[tag] = list(clean_tags[tag])
    return clean_tags


def _create_type_html(type, num_type, images, page_num, image_map, overwrite):
    """
    Creates an html page for a tag.
    """
    num_images = len(images)
    if num_images > 30:
        images = _get_images_table(images, image_map)
    else:
        images = "<br><br>".join(["<a href=../images/%s.html><img class='center-fit' src=../../images/%s></a>" % (x, image_map.get(x)) for x in images])
    url = ""
    try:
        url="%s/search/?sort=date-taken-desc&safe_search=1&tags=%s&user_id=%s&view_all=1" % (
            _FLICKR_URL,
            num_type,
            _get_flickr_id(),
        )
    except Exception as e:
        logging.error(
            "Could not create Flickr link for %s number of %s: %s" % (
                num_type,
                type,
                e.message,
            )
        )
    html = """
        <html>
            <head>
                <title>
                </title>
                {twitter_boostrap}
                <style>
                    {style}
                </style>
            </head>
            <body>
                <div class=padding>
                    <h1><a href={url}>{title}</a></h1>
                    <hr>
                    <a href=../index.html>Home</a> / <a href=../{type}s-{page_num}.html>Most {type}ed, page {page_num}</a>
                    <hr>
                    <p>
                        {photo_count} photo{plural}<br><br>
                    </p>
                    <div align=center class='imgbox'>
                        {images}
                    </div>
                </div>
            </body>
        </html>
    """.format(
        style="""
            .padding {
                padding: 50px 160px 50px 160px;
            }
            * {
                margin: 0;
                padding: 0;
            }
            .imgbox {
                display: grid;
                height: 100%;
            }
            .center-fit {
                max-width: 100%;
                max-height: 100vh;
                margin: auto;
            }
        """,
        type=type,
        plural="s" if num_images > 1 else "",
        twitter_boostrap=_TWITTER_BOOTSTRAP,
        title="Photos with %s %ss" % (num_type, type),
        page_num=page_num,
        photo_count=num_images,
        url=url,
        images=images,
    )
    _write_html(
        html,
        "./html/%ss/%s.html" % (type, num_type),
        overwrite=overwrite,
    )


def _create_types_page(type, cur_page_type, page_num, num_pages, image_map, overwrite):
    html = """
        <html>
            <head>
                <title>
                </title>
                {twitter_boostrap}
                <style>
                    {style}
                </style>
            </head>
            <body>
                <div class=padding>
                    <h1>Most {type}ed, page {page_num}</h1>
                    <hr>
                    <a href=index.html>Home</a>
                    <hr>
                    <center>{pages}</center>
                    <hr>
                    {types}
                    <hr>
                    <center>{pages}</center>
                </div>
            </body>
        </html>
    """.format(
        type=type,
        page_num=page_num,
        pages="Pages: " + " | ".join(["<a href=%ss-%s.html>%s</a>" % (type, x + 1, x + 1) for x in range(0, num_pages)]),
        style="""
            .padding {
                padding: 50px 160px 50px 160px;
            }
            * {
                margin: 0;
            }
            """,
        twitter_boostrap=_TWITTER_BOOTSTRAP,
        types=_get_table(type, cur_page_type, image_map),
    )
    _write_html(html, "./html/%ss-%s.html" % (type, str(page_num)), overwrite=overwrite)


def _create_types_html(type, types, image_map, overwrite):
    """
    Creates html pages for comments.
    """
    types_per_page = 100
    cur_page_num = 1
    count = 0
    cur_page_types = []
    num_pages = int(math.ceil(len(types.keys()) / types_per_page))
    for num_types, images in types.items():
        count += 1
        cur_page_types.append({"num": num_types, "images": images})
        if count == types_per_page:
            _create_types_page(type, cur_page_types, cur_page_num, num_pages, image_map, overwrite)
            cur_page_types = []
            count = 0
            cur_page_num += 1
        _create_type_html(
            type,
            num_types,
            images,
            cur_page_num,
            image_map,
            overwrite,
        )
    if len(cur_page_types) > 0:
        _create_types_page(type, cur_page_types, cur_page_num, num_pages, image_map, overwrite)


def _key_to_int(_dict):
    clean = {}
    for k, v in _dict.items():
        clean[int(k)] = v
    return clean


def run():
    """
    # Todo: option to make it only post public images/albums
    # Todo: add paging to albums
    # Todo: add home link to individual pages
    # Todo: (5 of 12345) Creating thumbnail image ...
    # Todo: cli for "overwrite" and other vars
    """

    _create_dirs()
    image_map = _create_image_map(write=True)
    _create_thumbnail_images(image_map, overwrite=False)
    _create_albums_symlinks(image_map)
    _create_profile_html(image_map)
    _create_albums_html(image_map)

    tags, favs, views, comments = _create_images_html(image_map, overwrite=False)
    # tags, favs, views, comments, image_map = _get_cache()  # For testing.

    tags = _combine_tags(tags)
    tags = _sort_by_value_len(tags)

    favs = _key_to_int(favs)
    favs = collections.OrderedDict(reversed(sorted(favs.items())))

    views = _key_to_int(views)
    views = collections.OrderedDict(reversed(sorted(views.items())))

    comments = _key_to_int(comments)
    comments = collections.OrderedDict(reversed(sorted(comments.items())))

    _create_tags_html(tags, image_map)
    _create_types_html("fav", favs, image_map, overwrite=True)
    _create_types_html("view", views, image_map, overwrite=True)
    _create_types_html("comment", comments, image_map, overwrite=True)

    logging.info("Done!")

    # _create_testimonials_html()
    # _create_contacts_html()
    # _create_followers_html()
    # _create_galleries_html()
    # _create_discussions_html()
    # _create_groups_html()


if __name__ == "__main__":
    try:
        log = _set_up_logging()
        run()
    except Exception as e:
        logging.error(
            "Something unexpected happened. Send %s to raphaelmatto@gmail.com for troubleshooting." % log
        )
        logging.error(e.message)
        logging.exception("Got exception on main handler:")
        raise
