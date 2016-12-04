tinymce.init({
    selector: '#my_editor',
    plugins: [
        'image lists',
        'fullscreen',
        'emoticons textcolor imageupload'
    ],
    menu: false,
    menubar: false,
    toolbar: 'bold italic | \
     alignleft aligncenter alignright | \
     bullist numlist | \ image | \
     forecolor backcolor emoticons |\
     fontsizeselect fullscreen | imageupload',
    nonbreaking_force_tab: true,
    imageupload_url: 'submit-image',
});
