from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from requests.exceptions import RequestException
import requests
from config.models import Device, ServiceCategory, ServiceOrder, Feedback
from django.db.models import Prefetch
from datetime import datetime
from django.utils.dateparse import parse_datetime
from django.db import models
from django.core.paginator import Paginator
from django.db.models import Q

# ============================
#          AUTH & HOME
# ============================

def home_page(request):
    return render(request, 'public/home.html')

def register_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            return render(request, "auth/register.html", {
                "error": "Password dan konfirmasi tidak cocok."
            })

        if User.objects.filter(username=username).exists():
            return render(request, "auth/register.html", {
                "error": "Username sudah digunakan."
            })

        User.objects.create_user(username=username, email=email, password=password1)
        return redirect("login")

    return render(request, "auth/register.html")


def login_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect("admin-dashboard")
            else:
                return redirect("dashboard_user")
        else:
            return render(request, "auth/login.html", {
                "error": "Username atau password salah."
            })

    return render(request, "auth/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


# ============================
#           USER AREA
# ============================

@login_required
def user_dashboard(request):
    if request.user.is_staff:
        return redirect("admin-dashboard")

    try:
        # Ambil semua pesanan dari API
        res = requests.get("http://127.0.0.1:8000/api/orders/")
        res.raise_for_status()
        all_orders = res.json()

        # Filter pesanan berdasarkan user yang login
        user_orders = [
            order for order in all_orders
            if str(order.get("device", {}).get("customer")) == str(request.user.id)
        ]

        # Siapkan statistik dengan key tanpa spasi (untuk keperluan template)
        stats = {
            "Pending": 0,
            "In_Progress": 0,
            "Finished": 0,
            "Cancelled": 0
        }

        for order in user_orders:
            status_key = order["status"].replace(" ", "_")  # Misalnya "In Progress" -> "In_Progress"
            if status_key in stats:
                stats[status_key] += 1

        # Ambil pesanan terakhir (jika ada), urutkan berdasarkan created_at descending
        user_orders_sorted = sorted(user_orders, key=lambda x: x.get("created_at", ""), reverse=True)
        last_order = user_orders_sorted[0] if user_orders_sorted else None

    except Exception as e:
        print("Gagal mengambil data dashboard:", e)
        stats = {
            "Pending": 0,
            "In_Progress": 0,
            "Finished": 0,
            "Cancelled": 0
        }
        last_order = None

    return render(request, "user/dashboard.html", {
        "stats": stats,
        "last_order": last_order,
    })

@login_required
def user_orders_by_status(request, status):
    if request.user.is_staff:
        return redirect('admin-dashboard')

    allowed_status = ['Pending', 'In Progress', 'Finished', 'Cancelled']
    if status not in allowed_status:
        return redirect('user_orders')

    orders = ServiceOrder.objects.filter(
        created_by=request.user,
        status=status
    ).select_related('device', 'category').order_by('-created_at')

    return render(request, "user/orders.html", {
        "orders": orders,
        "filter_status": status
    })

@login_required
def order_form(request):
    if request.user.is_staff:
        return redirect('admin-dashboard')

    error = None
    success = None

    # Ambil semua perangkat dan kategori servis
    devices = Device.objects.all()
    categories = ServiceCategory.objects.all()

    if request.method == "POST":
        device_id = request.POST.get("device")
        category_id = request.POST.get("category")
        description = request.POST.get("description")

        # Validasi input
        if not device_id or not category_id or not description:
            error = "Semua field wajib diisi."
        else:
            try:
                device = Device.objects.get(id=device_id)
                category = ServiceCategory.objects.get(id=category_id)

                ServiceOrder.objects.create(
                    device=device,
                    category=category,
                    description=description,
                    created_by=request.user
                )
                success = "Pesanan berhasil dikirim!"
            except Device.DoesNotExist:
                error = "Perangkat tidak ditemukan."
            except ServiceCategory.DoesNotExist:
                error = "Kategori tidak ditemukan."
            except Exception as e:
                error = f"Terjadi kesalahan: {e}"

    return render(request, "user/order_form.html", {
        "devices": devices,
        "categories": categories,
        "error": error,
        "success": success,
    })

@login_required
def user_orders(request):
    if request.user.is_staff:
        return redirect('admin-dashboard')

    try:
        # Ambil semua pesanan milik user berdasarkan created_by
        user_orders = ServiceOrder.objects.filter(
            created_by=request.user
        ).select_related('device', 'category').order_by('-created_at')

    except Exception as e:
        return render(request, "user/orders.html", {
            "orders": [],
            "error": f"Gagal mengambil data: {e}"
        })

    return render(request, "user/orders.html", {
        "orders": user_orders
    })

@login_required
def user_order_detail(request, order_id):
    if request.user.is_staff:
        return redirect("admin-dashboard")

    try:
        # Ambil order berdasarkan ID
        order = get_object_or_404(ServiceOrder, id=order_id)

        # Pastikan pesanan milik user yang sedang login
        if order.created_by != request.user:
            return redirect("user_orders")

    except Exception as e:
        return render(request, "user/order_detail.html", {
            "error": f"Gagal memuat detail pesanan: {e}"
        })

    return render(request, "user/order_detail.html", {
        "order": order
    })

@login_required
def user_order_history(request, order_id):
    if request.user.is_staff:
        return redirect("admin-dashboard")

    session = requests.Session()
    session.cookies.set("sessionid", request.COOKIES.get("sessionid"))

    try:
        # Ambil histori status
        res = session.get("http://127.0.0.1:8000/api/status-history/")
        res.raise_for_status()
        all_history = res.json()

        # Ambil detail order
        order_res = session.get(f"http://127.0.0.1:8000/api/orders/{order_id}/")
        order_res.raise_for_status()
        order = order_res.json()

        if str(order.get("created_by")) != str(request.user.id):
            return redirect("user_orders")

        # Filter histori untuk order ini
        history = [h for h in all_history if h["order"] == order_id]

        # Parse ISO datetime string ke objek datetime agar bisa diformat di template
        for h in history:
            if "timestamp" in h:
                h["parsed_timestamp"] = parse_datetime(h["timestamp"])

    except Exception as e:
        return render(request, "user/order_history.html", {
            "history": [],
            "order_id": order_id,
            "error": f"Gagal mengambil histori: {e}"
        })

    return render(request, "user/order_history.html", {
        "history": history,
        "order_id": order_id
    })

@login_required
def user_feedback_form(request):
    if request.user.is_staff:
        return redirect("admin-dashboard")

    success = None
    error = None

    # Hanya tampilkan order yang selesai dan belum dikasih feedback
    orders = ServiceOrder.objects.filter(
        created_by=request.user,
        status="Finished"
    ).exclude(feedback__isnull=False)

    if request.method == "POST":
        order_id = request.POST.get("order")
        rating = request.POST.get("rating")
        comment = request.POST.get("comment", "")

        if not order_id or not rating:
            error = "Semua field wajib diisi."
        else:
            try:
                import json
                session = requests.Session()

                # Kirim CSRF token dan sessionid ke header
                csrf_token = request.COOKIES.get("csrftoken")
                session.cookies.set("sessionid", request.COOKIES.get("sessionid"))
                session.cookies.set("csrftoken", csrf_token)

                res = session.post(
                    "http://127.0.0.1:8000/api/feedback/",
                    headers={
                        "Content-Type": "application/json",
                        "X-CSRFToken": csrf_token,
                    },
                    data=json.dumps({
                        "order": int(order_id),
                        "rating": int(rating),
                        "comment": comment
                    })
                )
                res.raise_for_status()
                success = "Feedback berhasil dikirim!"
            except Exception as e:
                error = f"Gagal mengirim feedback: {e}"

    return render(request, "user/feedback_form.html", {
        "orders": orders,
        "success": success,
        "error": error
    })

@login_required
def user_feedback_list(request):
    if request.user.is_staff:
        return redirect("admin-dashboard")

    from config.models import ServiceOrder, Feedback

    try:
        # Ambil semua feedback dari order milik user
        user_orders = ServiceOrder.objects.filter(created_by=request.user)
        feedbacks = Feedback.objects.filter(order__in=user_orders).select_related('order__device')

        formatted_feedbacks = []
        for fb in feedbacks:
            formatted_feedbacks.append({
                "device": fb.order.device,  # langsung tampilkan objek Device
                "rating": fb.rating,
                "comment": fb.comment
            })

    except Exception as e:
        return render(request, "user/feedback_list.html", {
            "feedbacks": [],
            "error": f"Gagal memuat feedback: {e}"
        })

    return render(request, "user/feedback_list.html", {
        "feedbacks": formatted_feedbacks
    })

# ============================
#          ADMIN AREA
# ============================

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect("dashboard_user")
    return render(request, 'admin/dashboard.html')


@login_required
def admin_orders_list(request):
    if not request.user.is_staff:
        return redirect("dashboard_user")

    search_query = request.GET.get("search", "")
    device_id = request.GET.get("device")

    orders = ServiceOrder.objects.select_related("device", "category", "created_by")

    if device_id:
        orders = orders.filter(device_id=device_id)

    if search_query:
        orders = orders.filter(
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(created_by__username__icontains=search_query)
        )

    orders = orders.order_by("-created_at")
    paginator = Paginator(orders, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    devices = Device.objects.all()

    return render(request, "admin/orders.html", {
        "orders": page_obj,
        "search_query": search_query,
        "selected_device": device_id,
        "devices": devices,
    })

@login_required
def admin_order_detail(request, order_id):
    if not request.user.is_staff:
        return redirect("dashboard_user")

    order = get_object_or_404(ServiceOrder, id=order_id)
    technicians = User.objects.filter(is_staff=True)

    if request.method == "POST":
        new_status = request.POST.get("status")
        technician_id = request.POST.get("technician")

        order.status = new_status

        try:
            order.technician = User.objects.get(id=technician_id) if technician_id else None
        except User.DoesNotExist:
            order.technician = None

        order.save()
        messages.success(request, "Pesanan berhasil diperbarui.")
        return redirect("admin-order-detail", order_id=order.id)

    status_choices = ServiceOrder.STATUS_CHOICES

    return render(request, "admin/order_detail.html", {
        "order": order,
        "technicians": technicians,
        "status_choices": status_choices,
    })

@login_required
def admin_feedback_list(request):
    if not request.user.is_staff:
        return redirect("dashboard_user")

    selected_device = request.GET.get("device")
    devices = Device.objects.all()
    feedbacks = Feedback.objects.select_related("order__device", "order__created_by")

    if selected_device:
        feedbacks = feedbacks.filter(order__device_id=selected_device)

    return render(request, "admin/feedback_list.html", {
        "devices": devices,
        "selected_device": selected_device,
        "feedbacks": feedbacks,
    })


@login_required
def admin_technician_list(request):
    if not request.user.is_staff:
        return redirect("dashboard_user")

    technicians = User.objects.filter(is_staff=False)

    return render(request, 'admin/technicians.html', {
        "technicians": technicians
    })

from config.models import ServiceOrder, UserProfile  