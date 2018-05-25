/**
 * @license Copyright (c) 2003-2018, CKSource - Frederico Knabben. All rights reserved.
 * For licensing, see https://ckeditor.com/legal/ckeditor-oss-license
 */

CKEDITOR.editorConfig = function( config ) {
	// Define changes to default configuration here. For example:
	// config.language = 'fr';
	// config.uiColor = '#AADC6E';
	// %REMOVE_START%
	config.language = 'zh-cn';
	config.uiColor = '#CAE1FF';
	config.height = 500;
	config.toolbarCanCollapse = true;

    //添加插件，多个插件用逗号隔开
    config.extraPlugins = 'codesnippet';
    //使用zenburn的代码高亮风格样式 PS:zenburn效果就是黑色背景
    //如果不设置着默认风格为default
    codeSnippet_theme: 'zenburn';
    config.filebrowserUploadUrl = '/ckupload/'
};
