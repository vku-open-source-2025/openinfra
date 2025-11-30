import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { usersApi } from "@/api/users";
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
import type { ProfileUpdateRequest } from "../../types/user";

const ProfileSettings: React.FC = () => {
    const queryClient = useQueryClient();
    const { user, setUser } = useAuthStore();
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
        }) => usersApi.changePassword(current, newPass),
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
            setErrors({ email: "Email is required" });
            return;
        }

        updateMutation.mutate(formData as ProfileUpdateRequest);
    };

    const handlePasswordSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setErrors({});

        if (!passwordData.current_password) {
            setErrors({ password: "Current password is required" });
            return;
        }
        if (
            !passwordData.new_password ||
            passwordData.new_password.length < 6
        ) {
            setErrors({
                password: "New password must be at least 6 characters",
            });
            return;
        }
        if (passwordData.new_password !== passwordData.confirm_password) {
            setErrors({ password: "Passwords do not match" });
            return;
        }

        changePasswordMutation.mutate({
            current: passwordData.current_password,
            new: passwordData.new_password,
        });
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
                    Profile Settings
                </h1>
                <p className="text-slate-500 mt-1">
                    Manage your account information
                </p>
            </div>

            <div className="bg-white rounded-lg border border-slate-200 p-6">
                <h2 className="text-lg font-semibold mb-4">
                    Profile Information
                </h2>
                <Form onSubmit={handleProfileSubmit}>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <FormField>
                            <FormLabel>Username</FormLabel>
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
                            <FormLabel required>Full Name</FormLabel>
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
                            <FormLabel>Phone</FormLabel>
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
                                ? "Updating..."
                                : "Update Profile"}
                        </Button>
                    </div>
                </Form>
            </div>

            <div className="bg-white rounded-lg border border-slate-200 p-6">
                <h2 className="text-lg font-semibold mb-4">Change Password</h2>
                <Form onSubmit={handlePasswordSubmit}>
                    <div className="space-y-4">
                        <FormField>
                            <FormLabel required>Current Password</FormLabel>
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
                            <FormLabel required>New Password</FormLabel>
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
                            <FormLabel required>Confirm New Password</FormLabel>
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
                                ? "Changing..."
                                : "Change Password"}
                        </Button>
                    </div>
                </Form>
            </div>
        </div>
    );
};

export default ProfileSettings;
