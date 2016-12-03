tinymce.init({
    selector: '#body',
    directionality: 'ltr',
    height: 400,
    plugins: [
        'image lists',
        'fullscreen nonbreaking',
        'emoticons textcolor'
    ],
    menu: false,
    menubar: false,
    toolbar: 'bold italic | \
     alignleft aligncenter alignright | \
     bullist numlist | \ image | \
     forecolor backcolor emoticons |\
     fontsizeselect fullscreen',
    fontsize_formats: '10pt 12pt 14pt 18pt 24pt 36pt',
    nonbreaking_force_tab: true
});