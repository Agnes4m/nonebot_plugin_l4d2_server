from amis import ColumnList, AmisList, ActionType, TableCRUD, TableColumn
from amis import Dialog, PageSchema, Switch, InputNumber, InputTag, Action, App
from amis import Form, InputText, InputPassword, DisplayModeEnum, Horizontal, Remark, Html, Page, AmisAPI, Wrapper,Combo,CRUD
from amis import LevelEnum, Select, InputArray, Alert, Tpl, Flex


from ..config import NICKNAME

logo = Html(html='''
<p align="center">
    <a href="https://github.com/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server">
        <img src="https://raw.githubusercontent.com/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server/main/image/logo.png"
         width="256" height="256" alt="Learning-Chat">
    </a>
</p>
<h1 align="center">Nonebot-Plugin-L4d2-Server 控制台</h1>
<div align="center">
    <a href="https://github.com/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server/" target="_blank">
    Github仓库</a>
</div>
<br>
<br>
''')
login_api = AmisAPI(
    url='/l4d2/api/login',
    method='post',
    adaptor='''
        if (payload.status == 0) {
            localStorage.setItem("token", payload.data.token);
        }
        return payload;
    '''
)

login_form = Form(api=login_api, title='', body=[
    InputText(name='username', label='用户名',
              labelRemark=Remark(shape='circle', content='后台管理用户名，默认为l4d2')),
    InputPassword(name='password', label='密码',
                  labelRemark=Remark(shape='circle', content='后台管理密码，默认为admin')),
], mode=DisplayModeEnum.horizontal, horizontal=Horizontal(left=3, right=9, offset=5), redirect='/l4d2/admin')
body = Wrapper(className='w-2/5 mx-auto my-0 m:w-full', body=login_form)
login_page = Page(title='', body=[logo, body])

global_config_form = Form(
    title='全局配置',
    name='global_config',
    initApi='/l4d2/api/chat_global_config',
    api='post:/l4d2/api/chat_global_config',
    body=[
        Switch(label='求生功能总开关', name='total_enable', value='${total_enable}', onText='开启', offText='关闭',
               labelRemark=Remark(shape='circle',
                                  content='关闭后，全局都将禁用求生功能。')),
        InputText(label='后台管理用户名', name='web_username', value='${web_username}',
                  labelRemark=Remark(shape='circle',
                                     content='登录本后台管理所需要的用户名。')),
        InputPassword(label='后台管理密码', name='web_password', value='${web_password}',
                      labelRemark=Remark(shape='circle',
                                         content='登录本后台管理所需要的密码。')),
        InputText(label='后台管理token密钥', name='web_secret_key', value='${web_secret_key}',
                  labelRemark=Remark(shape='circle',
                                     content='用于本后台管理加密验证token的密钥。')),
        InputText(label='查询key', name='l4_key', value='${l4_key}',
                  labelRemark=Remark(shape='circle',
                                     content='用于获取拓展功能的key。')),
        InputTag(label='求生上传地图用户', name='l4_master', value='${l4_master}',
                 enableBatchAdd=True,
                 placeholder='添加qq号', visibleOn='${total_enable}', joinValues=False, extractValue=True,
                 labelRemark=Remark(shape='circle',
                                    content='在这里加入的用户，才能上传地图')),
    ],
    actions=[Action(label='保存', level=LevelEnum.success, type='submit'),
             Action(label='重置', level=LevelEnum.warning, type='reset')]
)
group_select = Select(label='分群配置', name='group_id', source='${group_list}',
                      placeholder='选择群')
group_config_form = Form(
    title='分群配置（暂未完成）',
    visibleOn='group_id != null',
    initApi='/l4d2/api/chat_group_config?group_id=${group_id}',
    api='post:/l4d2/api/chat_group_config?group_id=${group_id}',
    body=[
        Switch(label='分群开关', name='enable', value='${enable}', onText='开启', offText='关闭',
               labelRemark=Remark(shape='circle', content='针对该群的群聊学习开关，关闭后，仅该群不会学习和回复。')),
        InputNumber(label='占位符', name='answer_threshold', value='${answer_threshold}', visibleOn='${enable}',
                    min=2,
                    labelRemark=Remark(shape='circle', content='单文本')),
        InputTag(label='占位符', name='ban_words', value='${ban_words}', enableBatchAdd=True,
                 placeholder='占位符，词条', visibleOn='${enable}', joinValues=False, extractValue=True,
                 labelRemark=Remark(shape='circle', content='占位符词条')),

    ],
    actions=[Action(label='保存', level=LevelEnum.success, type='submit'),
             ActionType.Ajax(
                 label='保存至所有群',
                 level=LevelEnum.primary,
                 confirmText='确认将当前配置保存至所有群？',
                 api='post:/l4d2/api/chat_group_config?group_id=all'
             ),
             Action(label='重置', level=LevelEnum.warning, type='reset')]
)

message_table = TableCRUD(
    mode='table',
    title='',
    syncLocation=False,
    api='/l4d2/api/get_chat_messages',
    interval=12000,
    footable=True,
    columns=[TableColumn(label='序号', name='message_id'),
            TableColumn(label='服务器ip', name='group_id', searchable=True),
            TableColumn(label='服务器端口', name='user_id', searchable=True),
            TableColumn(type='tpl', tpl='${raw_message|truncate:20}', label='rcon密码',
                        name='message',
                        searchable=True, popOver={'mode':      'dialog', 'title': '消息全文',
                                                    'className': 'break-all',
                                                    'body':      {'type': 'tpl',
                                                                'tpl':  '${raw_message}'}}),
            TableColumn(type='tpl', tpl='${time|date:YYYY-MM-DD HH\\:mm\\:ss}', label='时间',
                        name='time', sortable=True)
            ])

context_table = TableCRUD(mode='table',
                          title='',
                          syncLocation=False,
                          api='/l4d2/api/get_chat_contexts',
                          interval=60000,
                          footable=True,
                          itemActions=[ActionType.Url(
                                tooltip='加入游戏',
                                icon='fa fa-gamepad',
                                confirmText = "加入steam://connect/"+'${ip}',
                                url= "steam://connect/"+'${ip}',
                                # url= "http://"+'${ip}',
                                blank= True
                                 ),
                            ],
                          columns = [
                                    TableColumn(label='服主', name='tag', searchable=True),
                                    TableColumn(label='名称', name='name', searchable=True),
                                    TableColumn(label='地图', name='map_', searchable=True),
                                    TableColumn(label='玩家', name='rank_players', searchable=True),
                                    TableColumn(label='延迟', name='ping', searchable=True),
                                    TableColumn(label='IP 地址', name='ip', searchable=True),
                                    ])

message_page = PageSchema(url='/messages', icon='fa fa-comments', label='本地服务器管理',
                          schema=Page(title='本地服务器管理', body=[
                              Alert(level=LevelEnum.info,
                                    className='white-space-pre-wrap',
                                    body=(f'此数据库记录了{NICKNAME}所在服务器下的求生服务器。\n'

                                          f'· 功能暂未完善')),
                              message_table]))
context_page = PageSchema(url='/contexts', icon='fa fa-comment', label='远程服务器查询',
                          schema=Page(title='远程服务器查询',
                                      body=[Alert(level=LevelEnum.info,
                                                  className='white-space-pre-wrap',
                                                  body=(f'此数据库记录了{NICKNAME}所记录可查询的服务器ip。\n'
                                                        # '· 点击"回复列表"可以查看该条内容已学习到的可能的回复。\n'
                                                        # '· 点击"禁用"可以将该学习进行禁用，以后不会再学。\n'
                                                        f'· 功能暂未完善')),
                                            context_table]))

database_page = PageSchema(label='数据库', icon='fa fa-database',
                           children=[message_page, context_page])
config_page = PageSchema(url='/configs', isDefaultPage=True, icon='fa fa-wrench', label='配置',
                         schema=Page(title='配置', initApi='/l4d2/api/get_group_list',
                                     body=[global_config_form, group_select, group_config_form]))
chat_page = PageSchema(label='求生之路', icon='fa fa-wechat (alias)', children=[config_page, database_page])

github_logo = Tpl(className='w-full',
                  tpl='<div class="flex justify-between"><div></div><div><a href="https://github.com/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server" target="_blank" title="Copyright"><i class="fa fa-github fa-2x"></i></a></div></div>')
header = Flex(className='w-full', justify='flex-end', alignItems='flex-end', items=[github_logo])

admin_app = App(brandName='L4d2-Server',
                logo='https://raw.githubusercontent.com/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server/main/image/logo.png',
                header=header,
                pages=[{
                    'children': [config_page, database_page]
                }],
                footer='<div class="p-2 text-center bg-blue-100">Copyright © 2022 - 2023 <a href="https://github.com/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server" target="_blank" class="link-secondary">AGNES_DIGIAL</a> X<a target="_blank" href="https://github.com/baidu/amis" class="link-secondary" rel="noopener"> amis v2.2.0</a></div>')
