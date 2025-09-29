# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from .forms import DangKyForm
from django.urls import reverse_lazy

# Thêm một view cho trang chủ
def home_view(request):
    return render(request, 'home.html')

def dang_ky_view(request):
    if request.user.is_authenticated:
        return redirect('home') # Nếu đã đăng nhập, về trang chủ

    if request.method == 'POST':
        form = DangKyForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Tạo tài khoản thành công! Chào mừng {user.username}!")
            return redirect('home')
        else:
            messages.error(request, "Vui lòng kiểm tra lại thông tin đăng ký.")
    else:
        form = DangKyForm()
    return render(request, 'accounts/dang_ky.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'accounts/dang_nhap.html'
    redirect_authenticated_user = True

   
    def get_success_url(self):
        user = self.request.user
        messages.success(self.request, f"Đăng nhập thành công! Chào mừng trở lại, {user.username}.")

        # Nếu user là staff/admin, chuyển hướng đến trang Dashboard
        if user.is_staff:
            return reverse_lazy('admin_dashboard')
        
        # THAY ĐỔI TẠI ĐÂY: Nếu là người dùng thường, chuyển hướng về trang chủ
        else:
            return reverse_lazy('home')
        
    def form_invalid(self, form):
        messages.error(self.request, "Tên đăng nhập hoặc mật khẩu không đúng.")
        return super().form_invalid(form)