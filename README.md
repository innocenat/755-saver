# 755 Saver

This is a set of script design to saved all photos and video from 755 service.

This repository use https://github.com/kastden/nanagogo interface for
interacting with 755 API (vendored inside this repository).

## Install

Require requests>=2.21.0 as required by the `nanagogo` library.

## Usage

To save nanagogo to disk:

    python save.py [talk-id]

The `talk-id` can be found in the url https://7gogo.jp/[talk-id]. The script
can continue to update saved archive with new posts, but the comment, like,
and RT counts of saved posts will not be updated.

To create HTML file, run:

    python render.py [talk-id]

The saved raw file will be in `saved/[talk-id]`, and render HTML will be in
`saved/[talk-id]/html` folder.
