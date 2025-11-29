import { Link } from "react-router-dom";

const Footer = () => {
    return (
        <footer className="mx-0 my-0 h-64 mt-10 flex flex-col items-center justify-center max-lg:h-auto bg-white">
            <hr className="border-t border-[#bdbac0] w-full max-w-5xl mx-auto" />
            <div className="flex h-44 items-center justify-between px-10 w-full max-w-4xl mx-auto max-lg:flex-col max-lg:h-auto max-lg:items-start max-lg:my-6">
                <div className="flex flex-col items-start max-lg:my-2">
                    <p className="mb-4 text-sm font-semibold uppercase text-[#4c5664]">Khám phá</p>
                    <div className="flex flex-col space-y-3">
                        <Link to="/map" className="text-sm text-[#6C7580] flex w-fit items-center space-x-2 capitalize hover:underline">
                            Bản đồ hạ tầng
                        </Link>
                        <Link to="/docs" className="text-sm text-[#6C7580] flex w-fit items-center space-x-2 capitalize hover:underline">
                            API Documentation
                        </Link>
                    </div>
                </div>
                <div className="flex flex-col items-start max-lg:my-2">
                    <p className="mb-4 text-sm font-semibold uppercase text-[#4c5664]">Dự án</p>
                    <div className="flex flex-col space-y-3">
                        <a href="#about-us" className="text-sm text-[#6C7580] flex w-fit items-center space-x-2 capitalize hover:underline">
                            Giới thiệu
                        </a>
                        <a href="https://github.com/vku-open-source-2025/openinfra" target="_blank" rel="noopener noreferrer" className="text-sm text-[#6C7580] flex w-fit items-center space-x-2 capitalize hover:underline">
                            GitHub
                        </a>
                    </div>
                </div>
                <div className="flex flex-col items-start max-lg:my-2">
                    <p className="mb-4 text-sm font-semibold uppercase text-[#4c5664]">Giấy phép</p>
                    <div className="flex flex-col space-y-3">
                        <a href="https://opendatacommons.org/licenses/by/1-0/" target="_blank" rel="noopener noreferrer" className="text-sm text-[#6C7580] flex w-fit items-center space-x-2 capitalize hover:underline">
                            ODC-BY License
                        </a>
                        <span className="text-sm text-[#6C7580]">Dữ liệu mở</span>
                    </div>
                </div>
            </div>
            <div className="flex flex-col items-center mb-6">
                <p className="text-sm mb-2 text-[#4B5563]">Sản phẩm bởi đội ngũ VKU.OneLove</p>
                <p className="text-sm text-[#6C7580]">© OpenInfra 2025. Dữ liệu được cấp phép theo <a href="https://opendatacommons.org/licenses/by/1-0/" target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">ODC-BY</a>.</p>
            </div>
        </footer>
    );
};

export default Footer;
