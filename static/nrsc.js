document.addEventListener('DOMContentLoaded', function() {
    // Intersection Observer for section animations
    const sections = document.querySelectorAll('.nrsc-section');
    const navItems = document.querySelectorAll('.nav-item');
    
    const observerOptions = {
        root: null,
        threshold: 0.1,
        rootMargin: '0px'
    };

    const sectionObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                
                // Update navigation
                const currentId = entry.target.id;
                navItems.forEach(item => {
                    if (item.getAttribute('href') === `#${currentId}`) {
                        item.style.backgroundColor = 'rgba(0, 255, 157, 0.2)';
                        item.style.color = '#00ff9d';
                    } else {
                        item.style.backgroundColor = 'transparent';
                        item.style.color = '#fff';
                    }
                });
            }
        });
    }, observerOptions);

    sections.forEach(section => {
        sectionObserver.observe(section);
    });

    // Smooth scroll for navigation
    document.querySelectorAll('.nav-item').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            const navHeight = document.querySelector('.nrsc-nav').offsetHeight;
            
            window.scrollTo({
                top: targetSection.offsetTop - navHeight,
                behavior: 'smooth'
            });
        });
    });

    // Parallax effect for header
    window.addEventListener('scroll', () => {
        const header = document.querySelector('.header-background');
        const scrolled = window.pageYOffset;
        header.style.transform = `translate3d(0, ${scrolled * 0.5}px, 0)`;
    });
});
