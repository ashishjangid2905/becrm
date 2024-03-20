from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages, auth
from django.template import loader
from teams.models import Profile, Branch, User
from django.shortcuts import get_object_or_404
import datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@login_required(login_url='app:login')
def user_list(request):
    all_users = Profile.objects.all()

    context = {
        'all_users': all_users,
    }

    if not request.user.is_authenticated:
        return redirect('app:login')

    if request.user.role == 'admin':
        return render(request, 'admin/users.html', context)
    
@login_required(login_url='app:login')
def add_user(request):

    role_choices = User.ROLE
    department_choices = User.DEPARTMENT

    branch = Branch.objects.all()


    context = {
        'role_choices':role_choices,
        'department_choices': department_choices,
        'branch':branch,
    }

    if request.user.is_authenticated:
        if request.user.role == 'admin':
            if request.method == 'POST':
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                email = request.POST.get('email')
                role = request.POST.get('chooseRole')
                department = request.POST.get('chooseDepartment')
                password = request.POST.get('createPass')
                confirm_password = request.POST.get('confirmPass')
                if password != confirm_password:
                    messages.error(request,"Password do not match")
                    return redirect('teams:add_user')

                user = User.objects.create(first_name=first_name, last_name=last_name,email=email, role=role, department=department, password=make_password(password))
                
                branch_name = request.POST.get('chooseBranch')
                branch = get_object_or_404(Branch, branch_name=branch_name)

                profile = Profile.objects.create(user=user, branch=branch)
                return redirect('teams:users')
            return render(request, 'admin/add-user.html', context)
        return redirect('teams:add_user')
    

@login_required(login_url='app:login')
def edit_user(request, user_id):

    user_instance = get_object_or_404(User, pk=user_id)
    profile_instance = get_object_or_404(Profile, user=user_instance)
    role_choices = User.ROLE
    department_choices = User.DEPARTMENT

    chooseBranch = Branch.objects.all()


    context = {
        'role_choices':role_choices,
        'department_choices': department_choices,
        'chooseBranch':chooseBranch,
        'user_instance':user_instance,
        'profile_instance':profile_instance,
        
    }

    if request.user.is_authenticated:
        if request.user.role == 'admin':
            if request.method == 'POST':
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                email = request.POST.get('email')
                role = request.POST.get('chooseRole')
                department = request.POST.get('chooseDepartment')

                # Update the sample object with the new data

                user_instance.first_name = first_name
                user_instance.last_name = last_name
                user_instance.email = email
                user_instance.role = role
                user_instance.department = department

                user_instance.save()

                branch_name = request.POST.get('chooseBranch')
                branch_instance = get_object_or_404(Branch, branch_name=branch_name)
                user_profile = Profile.objects.get(user=user_instance)
                user_profile.branch = branch_instance

                user_profile.save()

                return redirect('teams:users')
            return render(request, 'admin/edit-user.html', context)
    else:
        return redirect('app:login')
    

# Change Password by User itself or admin

@login_required(login_url='app:login')
def change_password(request, user_id):
    if not request.user.is_authenticated:
        return redirect('app:login')
    
    user = get_object_or_404(User, pk=user_id)

    context = {
        'user_email':user
    }

    if request.user.role == 'admin':
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            if new_password != confirm_password:
                    messages.error(request,"Password do not match")
                    return redirect('teams:add_user')
            user.password = make_password(new_password)
            user.save()

            messages.success(request, 'Password has been Changed successfully')
            return redirect('teams:users')        

    return render(request, 'success/change-password.html', context)


@login_required(login_url='app:login')
def user_password(request):
    if not request.user.is_authenticated:
        return redirect('app:login')
    if not request.user.is_staff:
        user = request.user

        context = {
        'user_email':user
        }
        if request.method == 'POST':
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not check_password (old_password, user.password):
                messages.error(request, 'old Password do not match, Please try again')
                return redirect('teams:user_password')

            if new_password != confirm_password:
                    messages.error(request,"Password do not match")
                    return redirect('teams:user_password')
            user.password = make_password(new_password)
            user.save()

            update_session_auth_hash(request, user)

            messages.success(request, 'Password has been Changed successfully')
            return redirect('app:home')
    else:
        user = request.user

        context = {
        'user_email':user
        }
        if request.method == 'POST':
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not check_password (old_password, user.password):
                messages.error(request, 'old Password do not match, Please try again')
                return redirect('teams:user_password')

            if new_password != confirm_password:
                    messages.error(request,"Password do not match" )
                    return redirect('teams:user_password')
            user.password = make_password(new_password)
            user.save()

            update_session_auth_hash(request, user)

            messages.success(request, 'Password has been Changed successfully', extra_tags='user-password')

            return redirect('app:home')

    return render(request, 'success/change-password_user.html', context)