
/**************************************
*** git 常用快捷命令***
mkdir             -- 创建一个文件夹
pwd               -- 查看当前路径
git init          -- 创建git目录仓库
ls －ah           -- 查看含有.的文件夹等方式
git add           -- 将文件添加到仓库中
git commit -m ""  -- 将文件提交到仓库并添加注释
git diff          -- 查看当前文件的变化
git status        -- 查看当前仓库的状态
git log           -- 查看日志  
git log --pretty=oneline -- 单行显示日志
git log --graph --pretty=oneline --abbrev-commit  -- 能够查看到合并分支情况的查看日志方法
git reflog        -- 查看所有的行为
cat file          -- 查看文件内容
git diff HEAD -- file -- 查看当前版本和服务器最新版本的差异 
rm                -- 删除文件
git add .         -- 将所有的修改都提交到stage
ssh-keygen -t rsa -C "youremail@example.com" -- 创建SSH key
git push origin master -- 更新推送到github
git clone git@github.com:AblexLin/Ablex_Git.git 从远程仓库拷贝到本地
/************************************
git checkout -b filename -- 新建分支并切换到对应分支可以使用git branch/git status查看分支指向
  git branch branchname 创建分支
  git checkout branchname 切换到分支
git merge branchname  -- 合并分支到master上面去(合并的时候，当前必须在master分支上才能合并)
git merge --no-ff -m "注释" branchname --不适应fast forward方式合并分支，使用普通方式合并，合并后历史有分支，能够看出来曾经合并过！
git branch -d branchname -- 删除分支
git branch -D branchname -- 删除未合并的分支，强制删除
/***********************************
git stash          -- 保存当前的副本，让副本状态变成未修改到样子
git stash list     -- 查看之前保存的有多少
git stash apply    -- 恢复之前保存的stash，但是不会删除stash中的备份
git stash pop      -- 恢复之前保存的stash，并删除stash中的备份
git stash drop     -- 在使用了apply后可以使用这个drop来删除stash中的备份文件，按照堆栈方式删除
git stash apply stash@{0} -- 可以指定恢复哪一个备份的副本
/******************************************************************************/
版本回退
git reset --hard HEAD^
git reset --hard HEAD^^^
git reset --hard HEAD~100
git reset --hard commit_id
撤销修改
git checkout -- file
1.文件没有被add打时候执行，文件会被还原
2.文件已经被add但是还没有commit的时候执行，需要先执行git reset HEAD file将文件从
stage中退回到本地，再执行git checkout -- file就能够撤销修改了
/*****************************************************************************/
***************************************/
/--------分--------隔--------符--------/
/**************************************
*** vi编辑器使用常用快捷键***
:w                -- 保存文件但不退出vi
:w file           -- 将修改另外保存到file中，不退出vi
:w!               -- 强制保存，不推出vi
:wq               -- 保存文件并退出vi
:wq!              -- 强制保存文件，并退出vi
q:                -- 不保存文件，退出vi
:q!               -- 不保存文件，强制退出vi
:e!               -- 放弃所有修改，从上次保存文件开始再编辑
****************************************/

