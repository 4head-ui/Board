from django.shortcuts import render,get_object_or_404,redirect
from django.http import HttpResponse,Http404
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView,LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView,CreateView,DeleteView
from django.views.generic.base import TemplateView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView
from django.core.signing import  BadSignature
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator


from .models import AdvUser,Bb,SubRubric,Comment
from .forms import ChangeUserInfoForm,RegisterUserForm,SearchForm,BbForm,\
    AIFormSet,UserCommentForm,GuestCommentForm
from .utilities import signer
# Create your views here.

def index(request):
    bbs = Bb.objects.filter(is_active=True)[:10]
    paginator = Paginator(bbs, 3)
    if 'page' in request.GET:
        page_num = request.GET['page']
    else:
        page_num = 1
    page = paginator.get_page(page_num)
    context = {'bbs':bbs,'page':page}
    return render(request,'main/index.html',context)

def other_page(request,page):
    try:
        template=get_template('main/' + page + '.html')
    except TemplateDoesNotExist:
        raise Http404
    return HttpResponse(template.render(request=request))

class BBLoginView(LoginView):
    template_name = 'main/login.html'

@login_required
def profile(request):
    bbs = Bb.objects.filter(author=request.user.pk)
    paginator = Paginator(bbs, 3)
    if 'page' in request.GET:
        page_num = request.GET['page']
    else:
        page_num = 1
    page = paginator.get_page(page_num)
    context = {'bbs':bbs,'page':page}
    return render(request,'main/profile.html',context)

class BBLogoutView(LoginRequiredMixin,LogoutView):
    template_name = 'main/logout.html'


class ChangeUserInfoView(SuccessMessageMixin,LoginRequiredMixin,
                         UpdateView):
    model = AdvUser
    template_name = 'main/change_user_info.html'
    form_class = ChangeUserInfoForm
    success_url = reverse_lazy('main:profile')
    success_message = 'Личные данные изменены'

    def dispatch(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().dispatch(request,*args,**kwargs)

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset,pk=self.user_id)


class BBPasswordChangeView(SuccessMessageMixin,LoginRequiredMixin,
                           PasswordChangeView):

    template_name = 'main/password_change.html'
    success_url = reverse_lazy('main:profile')
    success_message = 'Пароль пользователя изменен'

class RegisterUserView(CreateView):
    model = AdvUser
    template_name = 'main/register_user.html'
    form_class = RegisterUserForm
    success_url = reverse_lazy('main:register_done')

class RegisterDoneView(TemplateView):
    template_name = 'main/register_done.html'


def user_activate(request,sign):
    try:
        username = signer.unsign(sign)
    except BadSignature:
        return render(request,'main/bad_signature.html')
    user = get_object_or_404(AdvUser,username=username)
    if user.is_activated:
        template = 'main/user_is_activated.html'
    else:
        template = 'main/activation_done.html'
        user.is_active = True
        user.is_activated = True
        user.save()
    return render(request,template)

class DeleteUserView(LoginRequiredMixin,DeleteView):
    model = AdvUser
    template_name = 'main/delete_user.html'
    success_url = reverse_lazy('main:index')


    def dispatch(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().dispatch(request,*args,**kwargs)


    def post(self,request,*args,**kwargs):
        logout(request)
        messages.add_message(request,messages.SUCCESS,'Пользователь'
                                                      ' удалён')
        return super().post(request,*args,**kwargs)

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset,pk=self.user_id)


def by_rubric(request,pk):
    rubric = get_object_or_404(SubRubric, pk=pk)
    bbs = Bb.objects.filter(is_active=True, rubric=pk)
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        q = Q(title__icontains=keyword) | Q(content__icontains=keyword)#Q Query запрос
        bbs = bbs.filter(q)
    else:
        keyword = ''
    form = SearchForm(initial={'keyword': keyword})
    paginator = Paginator(bbs, 3)
    if 'page' in request.GET:
        page_num=request.GET['page']
    else:
        page_num = 1
    page = paginator.get_page(page_num)
    context = {
        'rubric': rubric,
        'page': page,
        'bbs': page.object_list,
        'form': form,
    }
    return render(request, 'main/by_rubric.html', context)

def detail(request,rubric_pk,pk):
    bb = get_object_or_404(Bb,pk=pk)
    ais = bb.additionalimage_set.all() # (shell темка)
    # картинки связанные с бд и для джанго клинап
    comments = Comment.objects.filter(bb=pk,is_active=True)
    initial = {'bb':bb.pk}
    if request.user.is_authenticated:
        initial['author'] = request.user.username
        form_class = UserCommentForm
    else:
        form_class = GuestCommentForm
    form = form_class(initial=initial)
    if request.method == 'POST':
        c_form = form_class(request.POST)
        if c_form.is_valid():
            c_form.save()
            messages.add_message(request,messages.SUCCESS,'Комментарий'
                                                          ' добавлен')
        else:
            form = c_form
            messages.add_message(request, messages.WARNING, 'Комментарий'
                                                            ' не добавлен')
    context = {'bb':bb,'ais':ais,'comments':comments,'form':form}
    return render(request,'main/detail.html',context)

@login_required
def profile_bb_detail(request, rubric_pk, pk):
    bb = get_object_or_404(Bb, pk=pk)

    if request.method == 'POST':
        comment_pk = request.POST.get('comment', None)
        comment = Comment.objects.get(pk=comment_pk)
        comment.delete()
        messages.add_message(request, messages.SUCCESS, 'Комментарий удален')
    ais = bb.additionalimage_set.all()
    comments = Comment.objects.filter(bb=pk, is_active=True)
    #Список дополнительных изображений
    context = {'bb':bb,'ais':ais,'comments':comments}
    return render(request, 'main/profile_bb_detail.html', context)

@login_required
def profile_bb_add(request):
    if request.method == 'POST':
        form = BbForm(request.POST,request.FILES)
        if form.is_valid():
            bb = form.save()
            formset = AIFormSet(request.POST,request.FILES,instance=bb)
            # instance bb для того то бы изображение именно к этой объяве этого профиля
            if formset.is_valid():
                formset.save()
                messages.add_message(request,messages.SUCCESS,
                                     'Объявление добавлено')
                return redirect('main:profile')
    else:
        form = BbForm(initial={'author':request.user.pk})
        formset = AIFormSet()
    context = {'form':form,'formset':formset}
    return render(request,'main/profile_bb_add.html',context)

@login_required
def profile_bb_change(request,pk):
    bb = get_object_or_404(Bb,pk=pk)
    if request.method == 'POST':
        form = BbForm(request.POST,request.FILES,instance=bb)
        if form.is_valid():
            bb = form.save()
            formset = AIFormSet(request.POST,request.FILES,instance=bb)
            # instance bb для того то бы изображение именно к этой объяве этого профиля
            if formset.is_valid():
                formset.save()
                messages.add_message(request,messages.SUCCESS,
                                     'Объявление исправлено')
                return redirect('main:profile')
    else:
        form = BbForm(instance=bb)
        formset = AIFormSet(instance=bb)
    context = {'form':form,'formset':formset}
    return render(request,'main/profile_bb_change.html',context)

@login_required
def profile_bb_delete(request,pk):
    bb = get_object_or_404(Bb,pk=pk)
    if request.method == 'POST':
        bb.delete()
        messages.add_message(request, messages.SUCCESS,
                             'Объявление удалено')
        return redirect('main:profile')
    else:
        context = {'bb':bb}
        return render(request,'main/profile_bb_delete.html',context)

