import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { usersApi } from "@/api/users";
import { authApi } from "@/api/auth";
import {
    Form,
    FormField,
    FormLabel,
    FormError,
} from "../../components/ui/form";
import { Input } from "../../components/ui/input";
import { Button } from "../../components/ui/button";
import { Skeleton } from "../../components/ui/skeleton";
import { useAuthStore } from "../../stores/authStore";
import { useBiometricAuth } from "../../hooks/useBiometricAuth";
import type { ProfileUpdateRequest } from "../../types/user";
import { Fingerprint, ShieldCheck, ShieldOff } from "lucide-react";

const ProfileSettings: React.FC = () => {
    const queryClient = useQueryClient();
    const navigate = useNavigate();
    const { user, setUser, logout, accessToken, refreshToken } = useAuthStore();
    const {
        isAvailable: biometricAvailable,
        isEnabled: biometricEnabled,
        isLoading: biometricLoading,
        error: biometricError,
        registerBiometric,
        disableBiometric,
    } = useBiometricAuth();
    const [formData, setFormData] = useState<Partial<ProfileUpdateRequest>>({});
    const [passwordData, setPasswordData] = useState({
        current_password: "",
        new_password: "",
        confirm_password: "",
    });
    const [errors, setErrors] = useState<Record<string, string>>({});

    const { data: currentUser, isLoading } = useQuery({
        queryKey: ["current-user"],
        queryFn: () => usersApi.getCurrentUser(),
        enabled: !!user,
    });

    useEffect(() => {
        if (currentUser) {
            setFormData({
                email: currentUser.email,
                full_name: currentUser.full_name,
                phone: currentUser.phone,
            });
        }
    }, [currentUser]);

    const updateMutation = useMutation({
        mutationFn: (data: ProfileUpdateRequest) =>
            usersApi.updateCurrentUser(data),
        onSuccess: (updatedUser) => {
            setUser(updatedUser);
            queryClient.invalidateQueries({ queryKey: ["current-user"] });
            setErrors({});
        },
        onError: (error: any) => {
            if (error.response?.data?.detail) {
                setErrors({ submit: error.response.data.detail });
            }
        },
    });

    const changePasswordMutation = useMutation({
        mutationFn: ({
            current,
            new: newPass,
        }: {
            current: string;
            new: string;
        }) =>
            authApi.changePassword({
                current_password: current,
                new_password: newPass,
            }),
        onSuccess: () => {
            setPasswordData({
                current_password: "",
                new_password: "",
                confirm_password: "",
            });
            setErrors({});
        },
        onError: (error: any) => {
            if (error.response?.data?.detail) {
                setErrors({ password: error.response.data.detail });
            }
        },
    });

    const handleProfileSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setErrors({});

        if (!formData.email?.trim()) {
            setErrors({ email: "Email là bắt buộc" });
            return;
        }

        updateMutation.mutate(formData as ProfileUpdateRequest);
    };

    const handlePasswordSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setErrors({});

        if (!passwordData.current_password) {
            setErrors({ password: "Mật khẩu hiện tại là bắt buộc" });
            return;
        }
        if (
            !passwordData.new_password ||
            passwordData.new_password.length < 6
        ) {
            setErrors({
                password: "Mật khẩu mới phải có ít nhất 6 ký tự",
            });
            return;
        }
        if (passwordData.new_password !== passwordData.confirm_password) {
            setErrors({ password: "Mật khẩu không khớp" });
            return;
        }

        changePasswordMutation.mutate({
            current: passwordData.current_password,
            new: passwordData.new_password,
        });
    };

    const handleLogout = () => {
        logout();
        queryClient.clear();
        navigate({ to: "/" });
    };

    if (isLoading) {
        return (
            <div className="p-6 space-y-4">
                <Skeleton className="h-8 w-64" />
                <Skeleton className="h-64 w-full" />
            </div>
        );
    }

    return (
        <div className="p-6 space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-slate-900">
                    Cài đặt tài khoản
                </h1>
                <p className="text-slate-500 mt-1">
                    Quản lý thông tin tài khoản của bạn
                </p>
            </div>

            <div className="bg-white rounded-lg border border-slate-200 p-6">
                <h2 className="text-lg font-semibold mb-4">
                    Thông tin hồ sơ
                </h2>
                <Form onSubmit={handleProfileSubmit}>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <FormField>
                            <FormLabel>Tên đăng nhập</FormLabel>
                            <Input
                                value={currentUser?.username || ""}
                                disabled
                                className="bg-slate-50"
                            />
                        </FormField>

                        <FormField>
                            <FormLabel required>Email</FormLabel>
                            <Input
                                type="email"
                                value={formData.email || ""}
                                onChange={(e) =>
                                    setFormData({
                                        ...formData,
                                        email: e.target.value,
                                    })
                                }
                            />
                            {errors.email && (
                                <FormError>{errors.email}</FormError>
                            )}
                        </FormField>

                        <FormField>
                            <FormLabel required>Họ và tên</FormLabel>
                            <Input
                                value={formData.full_name || ""}
                                onChange={(e) =>
                                    setFormData({
                                        ...formData,
                                        full_name: e.target.value,
                                    })
                                }
                            />
                        </FormField>

                        <FormField>
                            <FormLabel>Số điện thoại</FormLabel>
                            <Input
                                value={formData.phone || ""}
                                onChange={(e) =>
                                    setFormData({
                                        ...formData,
                                        phone: e.target.value,
                                    })
                                }
                            />
                        </FormField>
                    </div>

                    {errors.submit && <FormError>{errors.submit}</FormError>}

                    <div className="flex gap-4 mt-6">
                        <Button
                            type="submit"
                            disabled={updateMutation.isPending}
                        >
                            {updateMutation.isPending
                                ? "Đang cập nhật..."
                                : "Cập nhật"}
                        </Button>
                    </div>
                </Form>
            </div>

            <div className="bg-white rounded-lg border border-slate-200 p-6">
                <h2 className="text-lg font-semibold mb-4">Đổi mật khẩu</h2>
                <Form onSubmit={handlePasswordSubmit}>
                    <div className="space-y-4">
                        <FormField>
                            <FormLabel required>Mật khẩu hiện tại</FormLabel>
                            <Input
                                type="password"
                                value={passwordData.current_password}
                                onChange={(e) =>
                                    setPasswordData({
                                        ...passwordData,
                                        current_password: e.target.value,
                                    })
                                }
                                placeholder="••••••••"
                            />
                        </FormField>

                        <FormField>
                            <FormLabel required>Mật khẩu mới</FormLabel>
                            <Input
                                type="password"
                                value={passwordData.new_password}
                                onChange={(e) =>
                                    setPasswordData({
                                        ...passwordData,
                                        new_password: e.target.value,
                                    })
                                }
                                placeholder="••••••••"
                            />
                        </FormField>

                        <FormField>
                            <FormLabel required>Xác nhận mật khẩu mới</FormLabel>
                            <Input
                                type="password"
                                value={passwordData.confirm_password}
                                onChange={(e) =>
                                    setPasswordData({
                                        ...passwordData,
                                        confirm_password: e.target.value,
                                    })
                                }
                                placeholder="••••••••"
                            />
                        </FormField>
                    </div>

                    {errors.password && (
                        <FormError>{errors.password}</FormError>
                    )}

                    <div className="flex gap-4 mt-6">
                        <Button
                            type="submit"
                            disabled={changePasswordMutation.isPending}
                        >
                            {changePasswordMutation.isPending
                                ? "Đang thay đổi..."
                                : "Đổi mật khẩu"}
                        </Button>
                    </div>
                </Form>
            </div>

            {/* Biometric Authentication Section */}
            {biometricAvailable && (
                <div className="bg-white rounded-lg border border-slate-200 p-6">
                    <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <Fingerprint className="w-5 h-5" />
                        Đăng nhập bằng sinh trắc học
                    </h2>
                    <p className="text-sm text-slate-500 mb-4">
                        Sử dụng vân tay hoặc nhận diện khuôn mặt để đăng nhập nhanh và an toàn
                    </p>
                    
                    <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                        <div className="flex items-center gap-3">
                            {biometricEnabled ? (
                                <ShieldCheck className="w-8 h-8 text-green-600" />
                            ) : (
                                <ShieldOff className="w-8 h-8 text-slate-400" />
                            )}
                            <div>
                                <p className="font-medium">
                                    {biometricEnabled ? 'Sinh trắc học đã bật' : 'Sinh trắc học chưa bật'}
                                </p>
                                <p className="text-sm text-slate-500">
                                    {biometricEnabled 
                                        ? 'Bạn có thể đăng nhập bằng vân tay hoặc nhận diện khuôn mặt' 
                                        : 'Bật để đăng nhập nhanh hơn lần sau'}
                                </p>
                            </div>
                        </div>
                        
                        {biometricEnabled ? (
                                <Button
                                variant="outline"
                                onClick={disableBiometric}
                                disabled={biometricLoading}
                            >
                                Tắt
                            </Button>
                        ) : (
                                <Button
                                onClick={async () => {
                                    if (currentUser && accessToken && refreshToken) {
                                        await registerBiometric(
                                            currentUser.username,
                                            accessToken,
                                            refreshToken,
                                            currentUser
                                        );
                                    }
                                }}
                                disabled={biometricLoading}
                            >
                                {biometricLoading ? 'Đang thiết lập...' : 'Bật'}
                            </Button>
                        )}
                    </div>
                    
                    {biometricError && (
                        <p className="text-sm text-red-600 mt-2">{biometricError}</p>
                    )}
                </div>
            )}

            <div className="bg-white rounded-lg border border-slate-200 p-6">
                <h2 className="text-lg font-semibold mb-4">Hành động tài khoản</h2>
                <div className="flex gap-4">
                        <Button
                        type="button"
                        variant="destructive"
                        onClick={handleLogout}
                    >
                        Đăng xuất
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default ProfileSettings;
