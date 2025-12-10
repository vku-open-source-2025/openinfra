import React from "react";
// import { Link } from 'react-router-dom';
import Footer from "../components/Footer";
import Header from "../components/Header";
import { Link } from "@tanstack/react-router";

interface TeamMember {
    name: string;
    avatar?: string;
}

const teamMembers: TeamMember[] = [
    {
        name: "Le Kim Hoang Trung",
        avatar: "/avatars/trung.jpg",
    },
    {
        name: "Dao Khanh Duy",
        avatar: "/avatars/duy.jpg",
    },
    {
        name: "Ho Sy Bao Nhan",
        avatar: "/avatars/nhan.jpg",
    },
];

const AboutUs: React.FC = () => {
    return (
        <div className="min-h-screen flex flex-col bg-white">
            <Header />

            {/* Hero Section - Clean & Light */}
            <section className="pt-32 pb-16 px-6">
                <div className="container mx-auto max-w-4xl text-center">
                    <h1 className="text-4xl md:text-5xl font-semibold text-slate-800 mb-4">
                        Về <span className="text-sky-500">OpenInfra</span>
                    </h1>
                    <p className="text-lg text-slate-500 max-w-2xl mx-auto">
                        Nền tảng quản lý hạ tầng mã nguồn mở dành cho đô thị thông minh
                    </p>
                </div>
            </section>

            {/* Mission - Simple */}
            <section className="py-12 px-6">
                <div className="container mx-auto max-w-3xl">
                    <div className="bg-sky-50/50 rounded-2xl p-8 md:p-12">
                        <h2 className="text-2xl font-semibold text-slate-700 mb-4">
                            Sứ mệnh của chúng tôi
                        </h2>
                        <p className="text-slate-600 leading-relaxed mb-4">
                            OpenInfra là hệ thống dựa trên GIS được xây dựng nhằm hỗ trợ
                            chính quyền địa phương quản lý và giám sát tài sản hạ tầng
                            công cộng trên khắp Việt Nam một cách hiệu quả.
                        </p>
                        <p className="text-slate-600 leading-relaxed">
                            Chúng tôi cung cấp giám sát IoT thời gian thực, bản đồ tương
                            tác và theo dõi bảo trì — được phát triển theo các chuẩn mở
                            để đảm bảo minh bạch và dễ tiếp cận.
                        </p>
                    </div>
                </div>
            </section>

            {/* Features - Minimal */}
            <section className="py-12 px-6">
                <div className="container mx-auto max-w-3xl">
                    <h2 className="text-2xl font-semibold text-slate-700 text-center mb-8">
                        Tính năng
                    </h2>
                    <div className="grid md:grid-cols-2 gap-4">
                        {[
                            "Bản đồ GIS tương tác",
                            "Tích hợp cảm biến IoT",
                            "Theo dõi bảo trì",
                            "API dữ liệu mở",
                        ].map((feature, idx) => (
                            <div
                                key={idx}
                                className="flex items-center gap-3 p-4 rounded-xl bg-white border border-slate-100"
                            >
                                <div className="w-2 h-2 rounded-full bg-sky-400"></div>
                                <span className="text-slate-600">
                                    {feature}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Team Section - Clean Cards */}
            <section className="py-16 px-6 bg-slate-50/50">
                <div className="container mx-auto max-w-4xl">
                    <h2 className="text-2xl font-semibold text-slate-700 text-center mb-3">
                        Đội ngũ
                    </h2>
                    <p className="text-slate-500 text-center mb-10">
                        Các bạn sinh viên VKU đam mê mã nguồn mở
                    </p>
                    <div className="grid md:grid-cols-3 gap-6">
                        {teamMembers.map((member, idx) => (
                            <div
                                key={idx}
                                className="bg-white rounded-xl p-6 text-center border border-slate-100"
                            >
                                <div className="w-20 h-20 mx-auto mb-4 rounded-full overflow-hidden bg-gradient-to-br from-sky-100 to-sky-200 flex items-center justify-center">
                                    {member.avatar ? (
                                        <img
                                            src={member.avatar}
                                            alt={member.name}
                                            className="w-full h-full object-cover"
                                            onError={(e) => {
                                                (
                                                    e.target as HTMLImageElement
                                                ).style.display = "none";
                                                (
                                                    e.target as HTMLImageElement
                                                ).parentElement!.innerHTML = `<span class="text-2xl font-medium text-sky-400">${
                                                    member.name
                                                        .split(" ")
                                                        .pop()
                                                        ?.charAt(0) || "?"
                                                }</span>`;
                                            }}
                                        />
                                    ) : (
                                        <span className="text-2xl font-medium text-sky-400">
                                            {member.name
                                                .split(" ")
                                                .pop()
                                                ?.charAt(0) || "?"}
                                        </span>
                                    )}
                                </div>
                                <h3 className="font-medium text-slate-700">
                                    {member.name}
                                </h3>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Sponsors - Simple */}
            <section className="py-16 px-6">
                <div className="container mx-auto max-w-4xl">
                    <h2 className="text-2xl font-semibold text-slate-700 text-center mb-3">
                        Đơn vị đồng hành
                    </h2>
                    <p className="text-slate-500 text-center mb-10">
                        Nhận được sự ủng hộ từ các tổ chức tin tưởng vào mã nguồn mở
                    </p>
                    <div className="flex flex-wrap justify-center items-center gap-8 md:gap-16">
                        <a
                            href="https://vku.udn.vn"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex flex-col items-center group"
                        >
                            <div className="bg-white rounded-xl p-6 border border-slate-100 hover:border-sky-200 transition-colors">
                                <img
                                    src="/vku-logo.svg"
                                    alt="VKU"
                                    className="h-16 w-auto object-contain opacity-80 group-hover:opacity-100 transition-opacity"
                                />
                            </div>
                            <span className="mt-3 text-sm text-slate-400">
                                Đại học VKU
                            </span>
                        </a>

                        <a
                            href="https://www.facebook.com/vaboratory"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex flex-col items-center group"
                        >
                            <div className="bg-white rounded-xl p-6 border border-slate-100 hover:border-sky-200 transition-colors">
                                <img
                                    src="/vic-logo.svg"
                                    alt="VIC"
                                    className="h-16 w-auto object-contain opacity-80 group-hover:opacity-100 transition-opacity"
                                />
                            </div>
                            <span className="mt-3 text-sm text-slate-400">
                                CLB IT VKU
                            </span>
                        </a>
                    </div>
                </div>
            </section>

            {/* CTA - Minimal */}
            <section className="py-12 px-6">
                <div className="container mx-auto max-w-2xl text-center">
                    <p className="text-slate-500 mb-6">
                        OpenInfra là dự án mở. Mọi đóng góp đều được trân trọng!
                    </p>
                    <div className="flex flex-wrap justify-center gap-3">
                        <a
                            href="https://github.com/vku-open-source-2025/openinfra"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 bg-slate-800 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-slate-700 transition-colors"
                        >
                            <svg
                                className="w-4 h-4"
                                fill="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                            </svg>
                            GitHub
                        </a>
                        <Link
                            to="/docs"
                            className="inline-flex items-center gap-2 bg-sky-500 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-sky-600 transition-colors"
                        >
                            Tài liệu API
                        </Link>
                        {/* <Link
                            to="/map"
                            className="inline-flex items-center gap-2 bg-white text-slate-600 px-5 py-2.5 rounded-lg text-sm font-medium border border-slate-200 hover:bg-slate-50 transition-colors"
                        >
                            View Map
                        </Link> */}
                    </div>
                </div>
            </section>

            {/* License - Subtle */}
            <section className="py-6 px-6 border-t border-slate-100">
                <div className="container mx-auto max-w-4xl text-center">
                    <p className="text-slate-400 text-xs">
                        Mã nguồn theo giấy phép{" "}
                        <a
                            href="https://www.apache.org/licenses/LICENSE-2.0"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sky-500 hover:underline"
                        >
                            Apache 2.0
                        </a>{" "}
                        · Dữ liệu theo giấy phép{" "}
                        <a
                            href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sky-500 hover:underline"
                        >
                            Open Government Licence v3.0 (OGL)
                        </a>
                    </p>
                </div>
            </section>

            <Footer />
        </div>
    );
};

export default AboutUs;
