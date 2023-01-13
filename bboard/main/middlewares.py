from .models import SubRubric

def bboard_context_processor(request):
    """ Добавление в контекст шаблонов переменной rubrics, содержащей все рубрики. """
    context = {}
    context['rubrics'] = SubRubric.objects.all()
    """Добавление в контекст шаблонов переменной keyword, со сформированным
     GET-параметром keyword, для генерирования 
    интернет-адресов в гиперссылках навигатора (для возврата к результатам 
    поиска). 
    И переменной all со сформированными GET-параметрами keyword и page, 
    которые мы добавим к интернет-адресам 
    гиперссылок, указывающих на страницы сведений об объявлениях (для возврата)
     """
    context['keyword'] = ''
    context['all'] = ''
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            context['keyword'] = '?keyword=' + keyword
            context['all'] = context['keyword']
    if 'page' in request.GET:
        page = request.GET['page']
        if page != '1':
            if context['all']:
                context['all'] += '&page=' + page
            else:
                context['all'] = '?page=' + page
    return context