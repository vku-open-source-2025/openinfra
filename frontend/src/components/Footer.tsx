import { Link } from "@tanstack/react-router";

const Footer = () => {
    return (
        <footer className="mx-0 my-0 h-64 mt-10 flex flex-col items-center justify-center max-lg:h-auto bg-white">
            <hr className="border-t border-[#bdbac0] w-full max-w-5xl mx-auto" />
            <div className="flex h-44 items-center justify-between px-10 w-full max-w-4xl mx-auto max-lg:flex-col max-lg:h-auto max-lg:items-start max-lg:my-6">
                <div className="flex flex-col items-start max-lg:my-2">
                    <p className="mb-4 text-sm font-semibold uppercase text-[#4c5664]">
                        Khám phá
                    </p>
                    <div className="flex flex-col space-y-3">
                        <Link
                            to="/map"
                            className="text-sm text-[#6C7580] flex w-fit items-center space-x-2 capitalize hover:underline"
                        >
                            Bản đồ hạ tầng
                        </Link>
                        <Link
                            to="/docs"
                            className="text-sm text-[#6C7580] flex w-fit items-center space-x-2 capitalize hover:underline"
                        >
                            Tài liệu API
                        </Link>
                    </div>
                </div>
                <div className="flex flex-col items-start max-lg:my-2">
                    <p className="mb-4 text-sm font-semibold uppercase text-[#4c5664]">
                        Dự án
                    </p>
                    <div className="flex flex-col space-y-3">
                        <a
                            href="#about-us"
                            className="text-sm text-[#6C7580] flex w-fit items-center space-x-2 capitalize hover:underline"
                        >
                            Giới thiệu
                        </a>
                        <a
                            href="https://github.com/vku-open-source-2025/openinfra"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-[#6C7580] flex w-fit items-center space-x-2 capitalize hover:underline"
                        >
                            GitHub
                        </a>
                    </div>
                </div>
                <div className="flex flex-col items-start max-lg:my-2">
                    <p className="mb-4 text-sm font-semibold uppercase text-[#4c5664]">
                        Đóng góp
                    </p>
                    <div className="flex flex-col space-y-3">
                        <a
                            href="https://contribution.openinfra.space/"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-[#6C7580] flex w-fit items-center space-x-2 capitalize hover:underline"
                        >
                            Gửi dữ liệu
                        </a>
                        <a
                            href="https://github.com/vku-open-source-2025/openinfra/issues"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-[#6C7580] flex w-fit items-center space-x-2 capitalize hover:underline"
                        >
                            Báo lỗi
                        </a>
                    </div>
                </div>
                <div className="flex flex-col items-start max-lg:my-2">
                    <p className="mb-4 text-sm font-semibold uppercase text-[#4c5664]">
                        Giấy phép
                    </p>
                    <div className="flex flex-col space-y-3">
                        <a
                            href="https://github.com/vku-open-source-2025/openinfra/blob/main/LICENSE"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-[#6C7580] flex w-fit items-center space-x-2 capitalize hover:underline"
                        >
                            Apache 2.0 (Mã nguồn)
                        </a>
                        <a
                            href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-[#6C7580] flex w-fit items-center space-x-2 capitalize hover:underline"
                        >
                            OGL (Dữ liệu)
                        </a>
                    </div>
                </div>
            </div>
            <div className="flex flex-col items-center mb-6">
                <p className="text-sm text-[#6C7580]">
                    © OpenInfra 2025. Mã nguồn theo giấy phép{" "}
                    <a
                        href="https://github.com/vku-open-source-2025/openinfra/blob/main/LICENSE"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-500 hover:underline"
                    >
                        Apache 2.0
                    </a>
                    . Dữ liệu theo giấy phép{" "}
                    <a
                        href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-500 hover:underline"
                    >
                        OGL
                    </a>
                    .
                </p>
            </div>
        </footer>
    );
};

export default Footer;
