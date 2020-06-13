if &cp | set nocp | endif
let s:cpo_save=&cpo
set cpo&vim
inoremap <C-W> u
inoremap <C-U> u
nnoremap <silent>  :nohlsearch=has('diff')?'|diffupdate':''
omap <silent> % <Plug>(MatchitOperationForward)
xmap <silent> % <Plug>(MatchitVisualForward)
nmap <silent> % <Plug>(MatchitNormalForward)
nnoremap <D-right> :vertical resize +5
nnoremap <D-up> :resize -5
nnoremap <D-down> :resize +5
nnoremap <D-left> :vertical resize -5
vnoremap < <gv
vnoremap > >gv
omap <silent> [% <Plug>(MatchitOperationMultiBackward)
xmap <silent> [% <Plug>(MatchitVisualMultiBackward)
nmap <silent> [% <Plug>(MatchitNormalMultiBackward)
omap <silent> ]% <Plug>(MatchitOperationMultiForward)
xmap <silent> ]% <Plug>(MatchitVisualMultiForward)
nmap <silent> ]% <Plug>(MatchitNormalMultiForward)
xmap a% <Plug>(MatchitVisualTextObject)
vnoremap fd 
omap <silent> g% <Plug>(MatchitOperationBackward)
xmap <silent> g% <Plug>(MatchitVisualBackward)
nmap <silent> g% <Plug>(MatchitNormalBackward)
nmap gcu <Plug>Commentary<Plug>Commentary
nmap gcc <Plug>CommentaryLine
omap gc <Plug>Commentary
nmap gc <Plug>Commentary
xmap gc <Plug>Commentary
vmap gx <Plug>NetrwBrowseXVis
nmap gx <Plug>NetrwBrowseX
nnoremap xs :OverCommandLine:%s
xmap <silent> <Plug>(MatchitVisualTextObject) <Plug>(MatchitVisualMultiBackward)o<Plug>(MatchitVisualMultiForward)
onoremap <silent> <Plug>(MatchitOperationMultiForward) :call matchit#MultiMatch("W",  "o")
onoremap <silent> <Plug>(MatchitOperationMultiBackward) :call matchit#MultiMatch("bW", "o")
xnoremap <silent> <Plug>(MatchitVisualMultiForward) :call matchit#MultiMatch("W",  "n")m'gv``
xnoremap <silent> <Plug>(MatchitVisualMultiBackward) :call matchit#MultiMatch("bW", "n")m'gv``
nnoremap <silent> <Plug>(MatchitNormalMultiForward) :call matchit#MultiMatch("W",  "n")
nnoremap <silent> <Plug>(MatchitNormalMultiBackward) :call matchit#MultiMatch("bW", "n")
onoremap <silent> <Plug>(MatchitOperationBackward) :call matchit#Match_wrapper('',0,'o')
onoremap <silent> <Plug>(MatchitOperationForward) :call matchit#Match_wrapper('',1,'o')
xnoremap <silent> <Plug>(MatchitVisualBackward) :call matchit#Match_wrapper('',0,'v')m'gv``
xnoremap <silent> <Plug>(MatchitVisualForward) :call matchit#Match_wrapper('',1,'v')m'gv``
nnoremap <silent> <Plug>(MatchitNormalBackward) :call matchit#Match_wrapper('',0,'n')
nnoremap <silent> <Plug>(MatchitNormalForward) :call matchit#Match_wrapper('',1,'n')
nnoremap <silent> <C-L> :nohlsearch=has('diff')?'|diffupdate':''
nnoremap <Plug>(lsp-signature-help) :call lsp#ui#vim#signature_help#get_signature_help_under_cursor()
nnoremap <Plug>(lsp-previous-reference) :call lsp#ui#vim#references#jump(-1)
nnoremap <Plug>(lsp-next-reference) :call lsp#ui#vim#references#jump(+1)
nnoremap <Plug>(lsp-status) :echo lsp#get_server_status()
nnoremap <Plug>(lsp-peek-implementation) :call lsp#ui#vim#implementation(1)
nnoremap <Plug>(lsp-implementation) :call lsp#ui#vim#implementation(0)
xnoremap <Plug>(lsp-document-range-format) :<Home>silent <End>call lsp#ui#vim#document_range_format()
nnoremap <Plug>(lsp-document-range-format) :set opfunc=lsp#ui#vim#document_range_format_opfuncg@
vnoremap <Plug>(lsp-document-format) :<Home>silent <End>call lsp#ui#vim#document_range_format()
nnoremap <Plug>(lsp-document-format) :call lsp#ui#vim#document_format()
nnoremap <Plug>(lsp-workspace-symbol) :call lsp#ui#vim#workspace_symbol()
nnoremap <Plug>(lsp-peek-type-definition) :call lsp#ui#vim#type_definition(1)
nnoremap <Plug>(lsp-type-hierarchy) :call lsp#ui#vim#type_hierarchy()
nnoremap <Plug>(lsp-type-definition) :call lsp#ui#vim#type_definition(0)
nnoremap <Plug>(lsp-rename) :call lsp#ui#vim#rename()
nnoremap <Plug>(lsp-references) :call lsp#ui#vim#references()
nnoremap <Plug>(lsp-previous-diagnostic) :call lsp#ui#vim#diagnostics#previous_diagnostic()
nnoremap <Plug>(lsp-next-diagnostic) :call lsp#ui#vim#diagnostics#next_diagnostic()
nnoremap <Plug>(lsp-previous-warning) :call lsp#ui#vim#diagnostics#previous_warning()
nnoremap <Plug>(lsp-next-warning) :call lsp#ui#vim#diagnostics#next_warning()
nnoremap <Plug>(lsp-previous-error) :call lsp#ui#vim#diagnostics#previous_error()
nnoremap <Plug>(lsp-next-error) :call lsp#ui#vim#diagnostics#next_error()
nnoremap <Plug>(lsp-preview-focus) :call lsp#ui#vim#output#focuspreview()
nnoremap <Plug>(lsp-preview-close) :call lsp#ui#vim#output#closepreview()
nnoremap <Plug>(lsp-hover) :call lsp#ui#vim#hover#get_hover_under_cursor()
nnoremap <Plug>(lsp-document-diagnostics) :call lsp#ui#vim#diagnostics#document_diagnostics()
nnoremap <Plug>(lsp-document-symbol) :call lsp#ui#vim#document_symbol()
nnoremap <Plug>(lsp-peek-definition) :call lsp#ui#vim#definition(1)
nnoremap <Plug>(lsp-definition) :call lsp#ui#vim#definition(0)
nnoremap <Plug>(lsp-peek-declaration) :call lsp#ui#vim#declaration(1)
nnoremap <Plug>(lsp-declaration) :call lsp#ui#vim#declaration(0)
nnoremap <Plug>(lsp-code-action) :call lsp#ui#vim#code_action()
nmap <silent> <Plug>CommentaryUndo :echoerr "Change your <Plug>CommentaryUndo map to <Plug>Commentary<Plug>Commentary"
vnoremap <silent> <Plug>NetrwBrowseXVis :call netrw#BrowseXVis()
nnoremap <silent> <Plug>NetrwBrowseX :call netrw#BrowseX(netrw#GX(),netrw#CheckIfRemote(netrw#GX()))
inoremap  u
inoremap  u
inoremap fd 
let &cpo=s:cpo_save
unlet s:cpo_save
set autoindent
set autoread
set background=dark
set backspace=indent,eol,start
set backupdir=~/.local/cache/vim,~/,/tmp
set clipboard=unnamed
set complete=.,w,b,u,t
set directory=~/.local/cache/vim,~/,/tmp
set display=lastline
set fileencodings=ucs-bom,utf-8,default,latin1
set formatoptions=tcqj
set helplang=fr
set history=1000
set incsearch
set laststatus=2
set listchars=tab:>\ ,trail:-,extends:>,precedes:<,nbsp:+
set nrformats=bin,hex
set packpath=/nix/store/8y81vkn5hnshhgs424d2wibkrxiswnrf-vim-pack-dir,~/.vim,/nix/store/6w3wm6pbi9bgamzkylfgp1q7svhd763j-vim_configurable-8.2.0013/share/vim/vimfiles,/nix/store/6w3wm6pbi9bgamzkylfgp1q7svhd763j-vim_configurable-8.2.0013/share/vim/vim82,/nix/store/6w3wm6pbi9bgamzkylfgp1q7svhd763j-vim_configurable-8.2.0013/share/vim/vimfiles/after,~/.vim/after
set ruler
set runtimepath=~/.config/vim,/nix/store/8y81vkn5hnshhgs424d2wibkrxiswnrf-vim-pack-dir/pack/home-manager/start/vim-colorschemes,/nix/store/8y81vkn5hnshhgs424d2wibkrxiswnrf-vim-pack-dir/pack/home-manager/start/vim-commentary,/nix/store/8y81vkn5hnshhgs424d2wibkrxiswnrf-vim-pack-dir/pack/home-manager/start/vim-lsp,/nix/store/8y81vkn5hnshhgs424d2wibkrxiswnrf-vim-pack-dir/pack/home-manager/start/vim-lsp-settings,/nix/store/8y81vkn5hnshhgs424d2wibkrxiswnrf-vim-pack-dir/pack/home-manager/start/vim-myftplugins-unstable,/nix/store/8y81vkn5hnshhgs424d2wibkrxiswnrf-vim-pack-dir/pack/home-manager/start/vim-qml,/nix/store/8y81vkn5hnshhgs424d2wibkrxiswnrf-vim-pack-dir/pack/home-manager/start/vim-sensible,/nix/store/6w3wm6pbi9bgamzkylfgp1q7svhd763j-vim_configurable-8.2.0013/share/vim/vim82/pack/dist/opt/matchit,~/.config/vim/after,/nix/store/6w3wm6pbi9bgamzkylfgp1q7svhd763j-vim_configurable-8.2.0013/share/vim,/nix/store/6w3wm6pbi9bgamzkylfgp1q7svhd763j-vim_configurable-8.2.0013/share/vim/vim82
set scrolloff=1
set sessionoptions=blank,buffers,curdir,folds,help,tabpages,winsize,terminal
set sidescrolloff=5
set smarttab
set tabpagemax=50
set tags=./tags;,./TAGS,tags,TAGS
set ttimeout
set ttimeoutlen=100
set viewoptions=folds,cursor,curdir
set viminfo=!,'100,<50,s10,h,n$XDG_CACHE_HOME/vim/viminfo
set wildignore=*.pyc
set wildmenu
set window=67
" vim: set ft=vim :
