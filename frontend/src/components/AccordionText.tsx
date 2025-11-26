import { useState } from 'react';

const AccordionText = () => {
    const [openIndex, setOpenIndex] = useState<number | null>(null);

    const faqs = [
        {
            question: "Hệ thống giám sát hạ tầng hoạt động như thế nào?",
            answer: "Hệ thống của chúng tôi sử dụng cảm biến IoT thời gian thực để giám sát tài sản hạ tầng và cung cấp cảnh báo ngay lập tức cho nhu cầu bảo trì."
        },
        {
            question: "Tôi có thể lập lịch công việc bảo trì không?",
            answer: "Có, bạn có thể lập lịch các công việc bảo trì và theo dõi trạng thái hoàn thành của chúng thông qua chế độ xem lịch."
        },
        {
            question: "Dữ liệu có được đồng bộ hóa theo thời gian thực không?",
            answer: "Có, tất cả dữ liệu hạ tầng được đồng bộ hóa theo thời gian thực bằng hệ thống backend Celery + Redis của chúng tôi."
        },
    ];

    return (
        <div className="max-w-3xl mx-auto my-16 px-4">
            {faqs.map((faq, index) => (
                <div key={index} className="mb-4 border border-gray-200 rounded-lg">
                    <button
                        onClick={() => setOpenIndex(openIndex === index ? null : index)}
                        className="w-full text-left px-6 py-4 flex justify-between items-center hover:bg-gray-50"
                    >
                        <span className="font-semibold text-[#4B5563]">{faq.question}</span>
                        <span className="text-[#4FACFE]">{openIndex === index ? '−' : '+'}</span>
                    </button>
                    {openIndex === index && (
                        <div className="px-6 pb-4 text-[#6C7580]">
                            {faq.answer}
                        </div>
                    )}
                </div>
            ))}
        </div>
    );
};

export default AccordionText;
