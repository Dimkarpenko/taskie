import asyncpg
import asyncio
from .encoder import hash_password, verify_password
from asyncpg import Record
import json

conn_string = ""

async def create_user(username, email, password):
    
    conn = await asyncpg.connect(conn_string)

    try:
        if await conn.fetchrow('SELECT id FROM users WHERE email = $1', email) == None:
            await conn.execute('''INSERT INTO users(username, email, password) VALUES($1, $2, $3)''', username, email, hash_password(password))
            return True
        
        return False
    
    except:
        pass

    finally:
        await conn.close()


async def login_user(email, password):
    conn = await asyncpg.connect(conn_string)

    try:
        user_password = await conn.fetchval("select password from users where email = $1", email)
        return verify_password(user_password, password)

    except:
        return None

    finally:
        await conn.close()

async def get_user_info(email, password):
    conn = await asyncpg.connect(conn_string)
    
    user_password = await conn.fetchval("select password from users where email = $1", email)
    if email==None or password == None:
        return None
    
    if verify_password(password, user_password):
        user_data = await conn.fetchrow("select id, username from users where email = $1", email)
        return {'username':user_data[1], 'user_id':user_data[0]}

    return None

async def create_project(user_id:int,title:str,description:str,tags:list,users:list, cover:str, video_url:str, additinoal_links:list):
    conn = await asyncpg.connect(conn_string)

    try:
        await conn.execute('''INSERT INTO projects (title, description, tags, author_id, users, additional_links, video_url, cover) VALUES($1, $2, $3, $4, $5, $6, $7, $8)''', title, description, ';'.join(tags), user_id, ';'.join(users), ';'.join(additinoal_links), video_url,cover)
        return True
    
    except Exception as e:
        print(e)
        return None

    finally:
        await conn.close()

async def get_projects(author_id):
    conn = await asyncpg.connect(conn_string)

    try:
        projects_ = []

        projects = await conn.fetch("select (id, title, cover, tags, users) from projects where author_id = $1", author_id)
        for project in projects:
            res = {}
            project = project[0]
            res['project_id'] = project[0]
            res['title'] = project[1]
            res['cover'] = "data:image/png;base64,"+project[2].decode()
            res['tags'] = project[3].split(";")
            res['authors'] = project[4].split(";")
            projects_.append(res)

        return projects_

    except Exception as e:
        print(e)
        return None

    finally:
        await conn.close()


async def get_project(project_id):
    conn = await asyncpg.connect(conn_string)

    try:
        project = await conn.fetchval("select (title, cover, tags, users, additional_links, video_url, author_id, description) from projects where id = $1", int(project_id))
        res = {}
        res['title'] = project[0]
        res['cover'] = "data:image/png;base64,"+project[1].decode()
        res['tags'] = project[2].split(";")
        res['authors'] = project[3].split(";")
        res['additional_links'] = project[4].split(";")
        res['video_url'] = project[5]
        res['author_id'] = project[6]
        res['description'] = project[7]

        return res

    except Exception as e:
        print(e)
        return None

    finally:
        await conn.close()


async def get_user(user_id):
    conn = await asyncpg.connect(conn_string)

    try:
        user_data = await conn.fetchval("select (username, email) from users where id = $1", int(user_id))
        projects = await conn.fetch("select (id, title) from projects where author_id = $1", int(user_id))

        res = {
            'username':user_data[0],
            'email':user_data[1],
            'projects': [{'title':x[0][1],'id':x[0][0]} for x in projects]
        }
        return res

    except Exception as e:
        print(e)
        return None

    finally:
        await conn.close()


async def check_board_access(author_id:int, project_id:int):
    conn = await asyncpg.connect(conn_string)

    res = await conn.fetchval('''select (author_id) from projects where id = $1''', project_id)
    if res != None:
        return res == author_id
    return None


async def push_cards(author_id:int,project_id:int, board_data:dict):
    conn = await asyncpg.connect(conn_string)

    try:
        await conn.execute('''INSERT INTO boards (author_id,project_id, board_data) VALUES ($1, $2, $3) ON CONFLICT (project_id) DO UPDATE SET board_data = EXCLUDED.board_data''', author_id,project_id, json.dumps(board_data, ensure_ascii=False))
        
        return True

    except Exception as e:
        print(e)
        return False

    finally:
        await conn.close()


async def fetch_cards(author_id:int, project_id:int):
    conn = await asyncpg.connect(conn_string)

    try:
        board_data = await conn.fetchval("select (board_data) from boards where project_id = $1 and author_id = $2", project_id, author_id)
        if board_data != None:
            board_data = json.loads(board_data)
            names = {'backlog':"Бэклог", 'todo':"Сделать", "working":"В работе", "done":"Готово"}
            res = [
                {
                    'id' : f'_{name}',
                    'title'  : names[name],
                    'class' : 'info',
                    'item'  : [{'id':name+"-"+str(ind+1),'title':data_[0],"description":data_[1]} for ind, data_ in enumerate(tuple(data))]
                } for name, data in board_data.items()
            ]
            return res
        
        return [
                {
                    'id' : '_backlog',
                    'title'  : 'Бэклог',
                    'class' : 'info',
                    'item'  : []
                },
                {
                    'id' : '_todo',
                    'title'  : 'Сделать',
                    'class' : 'info',
                    'item'  : []
                },
                {
                    'id' : '_working',
                    'title'  : 'В работе',
                    'class' : 'warning',
                    'item'  : []
                },
                {
                    'id' : '_done',
                    'title'  : 'Готово',
                    'class' : 'success',
                    'item'  : []
                }
            ]

    except Exception as e:
        print(e)
        return None

    finally:
        await conn.close()


if __name__ == "__main__":
    import asyncio

    print(asyncio.run(check_board_access(20,6)))