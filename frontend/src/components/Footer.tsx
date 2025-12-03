import { Link } from "@tanstack/react-router";

const Footer = () => {
    return (
        <footer className="mx-0 my-0 h-64 mt-10 flex flex-col items-center justify-center max-lg:h-auto bg-white">
            <hr className="border-t border-[#bdbac0] w-full max-w-5xl mx-auto" />
            <div className="flex h-44 items-center justify-between px-10 w-full max-w-4xl mx-auto max-lg:flex-col max-lg:h-auto max-lg:items-start max-lg:my-6">
                <div className="flex flex-col items-start max-lg:my-2">
                    <p className="mb-4 text-sm font-semibold uppercase text-[#4c5664]">
                        Explore
                    </p>
                    <div className="flex flex-col space-y-3">
                        <Link
                            to="/map"
                            className="text-sm text-[#6C7580] flex w-fit items-center space-x-2 capitalize hover:underline"
                        >
                            Infrastructure Map
                        </Link>
                        <Link
                            to="/docs"
                            className="text-sm text-[#6C7580] flex w-fit items-center space-x-2 capitalize hover:underline"
                        >
                            API Documentation
                        </Link>
                    </div>
                </div>
                <div className="flex flex-col items-start max-lg:my-2">
                    <p className="mb-4 text-sm font-semibold uppercase text-[#4c5664]">
                        Project
                    </p>
                    <div className="flex flex-col space-y-3">
                        <a
                            href="#about-us"
                            className="text-sm text-[#6C7580] flex w-fit items-center space-x-2 capitalize hover:underline"
                        >
                            About
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
                        Contribute
                    </p>
                    <div className="flex flex-col space-y-3">
                        <a
                            href="https://contribution.openinfra.space/"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-[#6C7580] flex w-fit items-center space-x-2 capitalize hover:underline"
                        >
                            Submit Data
                        </a>
                        <a
                            href="https://github.com/vku-open-source-2025/openinfra/issues"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-[#6C7580] flex w-fit items-center space-x-2 capitalize hover:underline"
                        >
                            Report Bug
                        </a>
                    </div>
                </div>
                <div className="flex flex-col items-start max-lg:my-2">
                    <p className="mb-4 text-sm font-semibold uppercase text-[#4c5664]">
                        License
                    </p>
                    <div className="flex flex-col space-y-3">
                        <a
                            href="https://github.com/vku-open-source-2025/openinfra/blob/main/LICENSE"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-[#6C7580] flex w-fit items-center space-x-2 capitalize hover:underline"
                        >
                            Apache 2.0 (Code)
                        </a>
                        <a
                            href="https://opendatacommons.org/licenses/by/1-0/"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-[#6C7580] flex w-fit items-center space-x-2 capitalize hover:underline"
                        >
                            ODC-BY (Data)
                        </a>
                    </div>
                </div>
            </div>
            <div className="flex flex-col items-center mb-6">
                <p className="text-sm text-[#6C7580]">
                    © OpenInfra 2025. Code licensed under{" "}
                    <a
                        href="https://github.com/vku-open-source-2025/openinfra/blob/main/LICENSE"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-500 hover:underline"
                    >
                        Apache 2.0
                    </a>
                    . Data licensed under{" "}
                    <a
                        href="https://opendatacommons.org/licenses/by/1-0/"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-500 hover:underline"
                    >
                        ODC-BY
                    </a>
                    .
                </p>
            </div>
        </footer>
    );
};

export default Footer;
