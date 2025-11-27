
import Footer from "../components/Footer";
import Header from "../components/Header";
import FeatureSection from "../components/FeatureSection";
import PromoteImage from "../components/PromoteImage";
import AccordionText from "../components/AccordionText";
import LandingPanel from "../components/LandingPanel";

import mapImage from "../assets/map.png";

const HomePage = () => {
    const featureContent = [
        {
            title: "Giám sát thời gian thực",
            subtitle: "Theo dõi tài sản hạ tầng của bạn trực tiếp",
            paragraphs: [
                "Giám sát tất cả tài sản hạ tầng của bạn theo thời gian thực với cảm biến IoT. Nhận thông báo ngay lập tức khi cần bảo trì.",
                "🚀 Hệ thống giám sát tiên tiến giúp bạn phòng ngừa sự cố trước khi chúng trở nên nghiêm trọng, tiết kiệm thời gian và chi phí.",
            ],
            imageUrl: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&auto=format&fit=crop",
            imageAlt: "Bảng điều khiển giám sát thời gian thực",
        },
        {
            title: "Lập lịch bảo trì",
            subtitle: "Không bao giờ bỏ lỡ công việc bảo trì",
            paragraphs: [
                "Lập lịch và theo dõi nhiệm vụ bảo trì với giao diện lịch trực quan.",
                "📅 Giữ đội ngũ của bạn luôn có tổ chức và đảm bảo mọi hạ tầng được bảo trì đúng lịch.",
            ],
            imageUrl: "https://images.unsplash.com/photo-1484480974693-6ca0a78fb36b?w=800&auto=format&fit=crop",
            imageAlt: "Lịch bảo trì",
        },
        {
            title: "Bản đồ tương tác",
            subtitle: "Trực quan hóa hạ tầng của bạn",
            paragraphs: [
                "Xem tất cả tài sản của bạn trên bản đồ tương tác với thông tin chi tiết và cập nhật trạng thái.",
                "🗺️ Dễ dàng định vị tài sản, lập kế hoạch tuyến đường và tối ưu hóa quy trình bảo trì với công cụ không gian địa lý.",
            ],
            imageUrl: "https://images.unsplash.com/photo-1524661135-423995f22d0b?w=800&auto=format&fit=crop",
            imageAlt: "Chế độ xem bản đồ tương tác",
        },
    ];

    return (
        <>
            <Header />
            <div className="pt-11 w-full min-h-screen">

                <PromoteImage img={mapImage} />
                <div className="w-full flex flex-col items-center">

                    <a
                        href="#features"
                        className="mx-8 text-base h-12 bg-gradient-to-b from-[#4FACFE] from-21% to-[#00F2FE] px-10 my-10 flex items-center rounded-full justify-center max-md:px-5 max-md:mx-5"
                    >
                        <p className="text-white font-semibold text-lg max-md:text-base">
                            Bắt đầu khám phá
                        </p>
                    </a>
                </div>
                <div className="text-center mt-32">
                    <div className="text-center text-2xl font-bold sm:text-5xl">
                        <h1 className="bg-gradient-to-r from-main-cyan from-21% to-main-blue bg-clip-text text-transparent mb-4">
                            Quản lý hạ tầng thông minh
                        </h1>
                        <h1 className="text-gray-heading">bắt đầu với công cụ tốt hơn.</h1>
                    </div>
                </div>

                <div id="features" className="p-20">
                    {featureContent.map((feature, index) => (
                        <FeatureSection
                            key={index}
                            imageOnRight={index % 2 === 0}
                            imageUrl={feature.imageUrl}
                            imageAlt={feature.imageAlt}
                            title={feature.title}
                            subtitle={feature.subtitle}
                            paragraphs={feature.paragraphs}
                        />
                    ))}
                </div>
            </div>
            <div className="space-y-3 text-center" id="faq">
                <p className="text-sm text-main-blue font-semibold">CÓ CÂU HỎI?</p>
                <h1 className="text-3xl font-semibold text-gray-heading sm:text-4xl">
                    Những điều bạn có thể thắc mắc
                </h1>
            </div>
            <AccordionText />
            <LandingPanel />
            <Footer />
        </>
    );
};

export default HomePage;
