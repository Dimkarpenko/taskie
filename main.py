import json, os, asyncio
from typing import Any

from fastapi import FastAPI, Request, HTTPException, status, UploadFile

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, PlainTextResponse, HTMLResponse, JSONResponse

from starlette.responses import Response

app = FastAPI(docs_url=None, redoc_url=None)

class NoCacheStaticFiles(StaticFiles):
    def __init__(self, *args: Any, **kwargs: Any):
        self.cachecontrol = "max-age=0, no-cache, no-store, must-revalidate"
        self.pragma = "no-cache"
        self.expires = "0"
        super().__init__(*args, **kwargs)

    def file_response(self, *args: Any, **kwargs: Any) -> Response:
        resp = super().file_response(*args, **kwargs)
        resp.headers.setdefault("Cache-Control", self.cachecontrol)
        resp.headers.setdefault("Pragma", self.pragma)
        resp.headers.setdefault("Expires", self.expires)
        return resp


app.mount("/assets",NoCacheStaticFiles(directory="assets"),name="assets")
templates = Jinja2Templates(directory="templates")


@app.exception_handler(404)
async def nf_handler(request, __):
    return templates.TemplateResponse("error.html", {"request": request, "status_code":404},status_code=404)

@app.exception_handler(401)
async def unauthorized_handler(request, __):
    return templates.TemplateResponse("error.html", {"request": request, "status_code":401},status_code=401)

@app.exception_handler(403)
async def denied_handler(request, __):
    return templates.TemplateResponse("error.html", {"request": request, "status_code":403},status_code=403)

@app.exception_handler(500)
async def ise_handler(request, __):
    return templates.TemplateResponse("error.html", {"request": request, "status_code":500},status_code=500)


@app.get("/")
async def home_page(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request}
    )

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html", {"request": request}
    )

@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html", {"request": request}
    )


@app.get("/project/{project_id}")
async def project_page(request: Request, project_id):
    from modules.db_manager import get_project

    project_data = await get_project(project_id)

    return templates.TemplateResponse(
        "project.html", {"request": request, "project_id":project_id} | project_data
    )


@app.get("/user/{user_id}")
async def user_page(request: Request, user_id):
    from modules.db_manager import get_user

    user_data = await get_user(user_id)

    return templates.TemplateResponse(
        "user.html", {"request": request, "user_id":user_id} | user_data
    )


@app.get("/account/")
async def tasks_page(request: Request):
    return RedirectResponse("/account/projects",status_code=301)


@app.get("/account/tasks/{project_id}")
async def tasks_page(request: Request,project_id):
    from modules.db_manager import get_user_info, check_board_access

    user_info = await get_user_info(request.cookies.get('email'),request.cookies.get('password'))
    user_access = await check_board_access(int(user_info['user_id']), int(project_id))

    if user_info != None:
        if user_access == None:
            return templates.TemplateResponse("error.html", {"request": request, "status_code":404},status_code=404)
        
        else:
            if user_access:
                return templates.TemplateResponse(
                    "tasks.html", {"request": request,  'title':"Задачи",'user_id':user_info['user_id'],'username':user_info['username'],'project_id':project_id}
                ) 

            return templates.TemplateResponse("error.html", {"request": request, "status_code":403},status_code=403)
        
    
    return RedirectResponse(url='/login')


@app.get("/account/projects")
async def projects_page(request: Request):
    from modules.db_manager import get_user_info, get_projects

    user_info = await get_user_info(request.cookies.get('email'),request.cookies.get('password'))

    if user_info != None:

        return templates.TemplateResponse(
            "projects.html", {"request": request,  'title':"Проекты",'user_id':user_info['user_id'],'username':user_info['username'], 'projects':await get_projects(user_info['user_id'])}
        ) 
    
    return RedirectResponse(url='/login')


@app.get("/account/projects/new")
async def projects_page(request: Request):
    from modules.db_manager import get_user_info

    user_info = await get_user_info(request.cookies.get('email'),request.cookies.get('password'))

    if user_info != None:
        return templates.TemplateResponse(
            "project_editor.html", {"request": request,  'title':"Проекты",'username':user_info['username'], 'user_id':user_info['user_id']}
        ) 
    
    return RedirectResponse(url='/login')


@app.get('/account/logout',response_class=RedirectResponse)
async def delete_cookie():
    resp = RedirectResponse('/account/')
    resp.delete_cookie(key="password")
    return resp


@app.post('/api/board/fetch_cards')
async def fetch_cards(request: Request):
    from modules.db_manager import fetch_cards

    data = await request.json()
    board_data = await fetch_cards(int(data['author_id']),int(data['project_id']))
    # print(board_data)
    return board_data


@app.post('/api/board/push_cards')
async def push_cards(request: Request):
    from modules.db_manager import push_cards

    data = await request.json()
    board_data = await push_cards(int(data['author_id']),int(data['project_id']),data['boards'])
    return board_data


@app.post('/api/new_project')
async def register_api(request: Request):
    from modules.image_handler import handle_image
    from modules.db_manager import create_project

    data = await request.form()

    await create_project(int(data['author_id']), data['title'], data['description'], data['tags'].split(" "), data['users'].split(" "), handle_image(data['files'].file), data['video_url'], [data['link_1'],data['link_2']])
    return RedirectResponse('/account/projects', status_code=301)


@app.post('/api/register')
async def register_api(request: Request):
    from modules.db_manager import create_user
    data = await request.form()

    if await create_user(data['username'],data['email'],data['password']):
        return JSONResponse(content={},status_code=200)
    
    return JSONResponse(content={},status_code=401)

@app.post('/api/login')
async def login_api(request: Request, response: Response):

    from modules.db_manager import login_user
    from modules.encoder import hash_password

    data = await request.form()
    
    is_correct = await login_user(data['email'],password=data['password'])

    if is_correct:
        response = JSONResponse(content={},status_code=200)
        response.set_cookie(key='email', value=data['email'], httponly=True)
        response.set_cookie(key='password', value=hash_password(hash_password(data['password'])), httponly=True)
        return response
    else:
        return JSONResponse(content={},status_code=401)
    


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app,host='0.0.0.0',port=4000)