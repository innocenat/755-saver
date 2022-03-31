from nanagogo import NanagogoTalk, NanagogoError
import time
import os, os.path
import json
import urllib.request

PATH = 'saved/{}'

POST_TYPE_TXT = 1
POST_TYPE_STK = 2
POST_TYPE_IMG = 3
POST_TYPE_QA  = 4
POST_TYPE_RT  = 5
POST_TYPE_VID = 6
POST_TYPE_CB  = 7
POST_TYPE_CB2 = 8

POST_TYPE_USER_JOIN = 101
POST_TYPE_USER_LEFT = 102
POST_TYPE_USER_INIT = 104   # Not sure

BODY_TYPE_TXT = 1
BODY_TYPE_STK = 2
BODY_TYPE_IMG = 3
BODY_TYPE_QA  = 4
BODY_TYPE_CB  = 7
BODY_TYPE_VID = 8
BODY_TYPE_LNK = 10

def post_error(post):
    print('Unable to process post {}!'.format(post['post']['postId']))
    print(json.dumps(post))

def make_content(post_id, body, path):
    if body['bodyType'] == BODY_TYPE_TXT:
        return {'text': body['text']}
    if body['bodyType'] == BODY_TYPE_STK:
        # Save sticker
        img_url = body['image']
        filename = '{}/media/{}{}'.format(path, post_id, os.path.splitext(img_url)[1])
        if not os.path.exists(filename):
            urllib.request.urlretrieve(img_url, filename)
        return {'sticker': 'media/{}{}'.format(post_id, os.path.splitext(img_url)[1])}
    if body['bodyType'] == BODY_TYPE_IMG:
        # Save image
        img_url = body['image']
        filename = '{}/media/{}{}'.format(path, post_id, os.path.splitext(img_url)[1])
        if not os.path.exists(filename):
            urllib.request.urlretrieve(img_url, filename)
        return {'image': 'media/{}{}'.format(post_id, os.path.splitext(img_url)[1])}
    if body['bodyType'] == BODY_TYPE_QA:
        return {'name': body['comment']['user']['name'], 'time': body['comment']['comment']['time'], 'comment': body['comment']['comment']['body']}
    if body['bodyType'] == BODY_TYPE_VID:
        # Save image
        vid_url = body['movieUrlHq']
        filename = '{}/media/{}{}'.format(path, post_id, os.path.splitext(vid_url)[1])
        if not os.path.exists(filename):
            urllib.request.urlretrieve(vid_url, filename)
        return {'video': 'media/{}{}'.format(post_id, os.path.splitext(vid_url)[1])}
    if body['bodyType'] == BODY_TYPE_LNK:
        return {'url': body['url']}
    print('Unable to process body!')
    print(json.dumps(body))
        

def save_post(post, path, useUUID = False):
    # Epoch
    if post['post']['postId'] == 1:
        return {'epoch': True}

    # print(post)
    pp = {
        'id': post['post']['postId'] if not useUUID else '{}-{}'.format(post['post']['talkId'], post['post']['postId']),
        'name': post['user']['name'],
        'time': post['post']['time'],
        'rtCount': post['post']['rtCount'],
        'likeCount': post['post']['likeCount'],
        'commentCount': post['post']['commentCount'],
    }

    # Standard text post
    if post['post']['postType'] == POST_TYPE_TXT:
        if len(post['post']['body']) != 1 or (post['post']['body'][0]['bodyType'] != BODY_TYPE_TXT and post['post']['body'][0]['bodyType'] != BODY_TYPE_LNK):
            # Somehow this can be a combi post, so process as combi
            pp['content'] = [
                make_content(pp['id'], x, path) for x in post['post']['body']
            ]
            return pp
        pp['content'] = make_content(pp['id'], post['post']['body'][0], path)
        return pp

    # Sticker post
    if post['post']['postType'] == POST_TYPE_STK:
        if len(post['post']['body']) != 1 or post['post']['body'][0]['bodyType'] != BODY_TYPE_STK:
            post_error(post)
            return {'error': True}
        pp['content'] = make_content(pp['id'], post['post']['body'][0], path)
        return pp

    # Image post
    if post['post']['postType'] == POST_TYPE_IMG:
        if len(post['post']['body']) != 1 or post['post']['body'][0]['bodyType'] != BODY_TYPE_IMG:
            post_error(post)
            return {'error': True}
        pp['content'] = make_content(pp['id'], post['post']['body'][0], path)
        return pp

    # QA post
    if post['post']['postType'] == POST_TYPE_QA:
        if len(post['post']['body']) < 2 or post['post']['body'][0]['bodyType'] != BODY_TYPE_QA:
            post_error(post)
            return {'error': True}
        pp['content'] = [
            make_content(pp['id'], x, path) for x in post['post']['body']
        ]
        return pp
    
    # RT post
    if post['post']['postType'] == POST_TYPE_RT:
        if len(post['post']['body']) != 1:
            post_error(post)
            return {'error': True}
        pp['original'] = save_post(post['post']['body'][0], path, True)
        return pp

    # Video post
    if post['post']['postType'] == POST_TYPE_VID:
        if len(post['post']['body']) != 1 or post['post']['body'][0]['bodyType'] != BODY_TYPE_VID:
            post_error(post)
            return {'error': True}
        pp['content'] = make_content(pp['id'], post['post']['body'][0], path)
        return pp

    # Combi post
    if post['post']['postType'] == POST_TYPE_CB or post['post']['postType'] == POST_TYPE_CB2:
        pp['content'] = [
            make_content(pp['id'], x, path) for x in post['post']['body']
        ]
        return pp

    # User join the talk
    if post['post']['postType'] == POST_TYPE_USER_JOIN:
        return {'user_join': post['user']['name'], 'id': pp['id']}

    # User left the talk
    if post['post']['postType'] == POST_TYPE_USER_LEFT:
        return {'user_left': post['user']['name'], 'id': pp['id']}

    # Unknown but exists in older talk at post #2
    if post['post']['postType'] == POST_TYPE_USER_INIT:
        return {'unknown': True, 'id': pp['id']}

    post_error(post)
    return {'error': True}


def save_talk(talk, path, limit = 5, last_saved_id = 0):
    nt = NanagogoTalk(talk)

    posts = []

    i = 0
    if limit == 0:
        for page in nt.iterfeed():
            i += 1
            print('Processing page {}...'.format(i))
            for node in page:
                if node['post']['postId'] == last_saved_id:
                    return posts, nt.info['talk']['name']
                posts.append(save_post(node, path))
            time.sleep(1)
    else:
        for node in nt.feed(count=limit):
            if node['post']['postId'] == last_saved_id:
                return posts
            posts.append(save_post(node, path))

    return posts, nt.info['talk']['name']

def save_talk_to(talk, path):
    if not os.path.exists(path):
        os.makedirs(path)
    if not os.path.exists(path + '/media'):
        os.makedirs(path + '/media')

    # Check last saved
    last_saved_id = 0
    last_saved_path = '{}/saved_until'.format(path)
    if os.path.exists(last_saved_path):
        with open(last_saved_path, encoding='utf-8') as fp:
            last_saved_id = int(fp.read())

    # Read posts
    posts, talk_name = save_talk(talk, path, 0, last_saved_id)

    existing_posts = []
    existing_posts_path = '{}/posts.json'.format(path)
    if os.path.exists(existing_posts_path):
        with open(existing_posts_path, encoding='utf-8') as fp:
            existing_posts = json.load(fp)
    
    posts = posts + existing_posts

    # Write last saved
    last_saved_id = posts[0]['id']
    with open(last_saved_path, 'w', encoding='utf-8') as fp:
        fp.write(str(last_saved_id))

    # Write posts
    with open(existing_posts_path, 'w', encoding='utf-8') as fp:
        json.dump(posts, fp)

    # Write talk name
    talk_name_file = '{}/name.txt'.format(path)
    with open(talk_name_file, 'w', encoding='utf-8') as fp:
        fp.write(talk_name)
    
def save_with_check(path):
    try:
        nt = NanagogoTalk(path)
        nt.info # To trigger exception if not exist
        print('Saving {}...'.format(path))
        save_talk_to(path, PATH.format(path))
        return 0
    except NanagogoError:
        print('Talk {} does not exists!'.format(path))
        return 1

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: python save.py talk_id')
    else:
        if sys.argv[1] == 'all':
            path = PATH.format('')
            subfolders = [f.name for f in os.scandir(path) if f.is_dir()]
            for t in subfolders:
                save_with_check(t)
        else:
            result = save_with_check(sys.argv[1])
            if result == 1:
                sys.exit(result)
