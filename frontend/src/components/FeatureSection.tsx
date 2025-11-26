interface FeatureSectionProps {
    imageOnRight: boolean;
    imageUrl: string;
    imageAlt: string;
    title: string;
    subtitle: string;
    paragraphs: string[];
}

const FeatureSection = ({
    imageOnRight,
    imageUrl,
    imageAlt,
    title,
    subtitle,
    paragraphs,
}: FeatureSectionProps) => {
    return (
        <div className={`flex items-center gap-8 my-16 ${imageOnRight ? 'flex-row' : 'flex-row-reverse'} max-lg:flex-col`}>
            <div className="flex-1">
                <img src={imageUrl} alt={imageAlt} className="w-full rounded-lg" />
            </div>
            <div className="flex-1">
                <h3 className="text-3xl font-bold text-gray-heading mb-2">{title}</h3>
                <p className="text-xl text-main-blue font-semibold mb-4">{subtitle}</p>
                {paragraphs.map((para, idx) => (
                    <p key={idx} className="text-gray-text mb-3">
                        {para}
                    </p>
                ))}
            </div>
        </div>
    );
};

export default FeatureSection;
