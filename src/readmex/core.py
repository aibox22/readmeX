import os
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from readmex.utils.model_client import ModelClient
from readmex.utils.file_handler import (
    find_files,
    get_project_structure,
    load_gitignore_patterns,
)
from readmex.utils.dependency_analyzer import DependencyAnalyzer
from readmex.utils.logo_generator import generate_logo
from readmex.utils.language_analyzer import LanguageAnalyzer
from readmex.config import load_config

from readmex.config import (
    DEFAULT_IGNORE_PATTERNS,
    SCRIPT_PATTERNS,
    DOCUMENT_PATTERNS,
    get_readme_template_path,
)


class readmex:
    def __init__(self, project_dir=None, silent=False, debug=False):
        self.model_client = ModelClient(
            quality="hd", image_size="1024x1024"
        )  # 确保使用高质量、高分辨率图像生成
        self.console = Console()
        self.project_dir = project_dir  # 初始化时设置项目目录
        self.output_dir = None  # 输出目录将在 _get_basic_info 中设置
        self.silent = silent  # 静默模式，不进行交互式输入
        self.debug = debug  # 调试模式，不调用大模型
        self.language_analyzer = LanguageAnalyzer()  # Initialize language analyzer
        self.primary_language = None  # Store primary programming language
        self.config = {
            "github_username": "",
            "repo_name": "",
            "project_title": "",
            "twitter_handle": "",
            "linkedin_username": "",
            "email": "",
            "readme_language": "",
            "project_description": "",
            "entry_file": "",
            "key_features": "",
            "additional_info": "",
        }

    def generate(self, project_path=None):
        """Generate README for the project."""
        self.console.print(
            "[bold green]🚀 Starting AI README generation...[/bold green]"
        )

        # Set project directory if provided
        if project_path:
            self.project_dir = project_path

        # Load configuration: environment variables > config file > user input
        self._load_configuration()

        # Get basic project information if not already set
        if not self.project_dir or not self.output_dir:
            self._get_basic_info()

        # Collect information
        self._get_git_info()
        self._get_user_info()
        self._get_project_meta_info()

        # Analyze project languages first to determine primary language
        self._analyze_project_languages()

        # Analyze project
        structure = self._get_project_structure()
        dependencies = self._get_project_dependencies()
        descriptions = self._get_script_descriptions()
        # Default readme language is English
        if not self.config["readme_language"]:
            self.config["readme_language"] = "en"

        # Auto-generate project description if empty
        if not self.config["project_description"]:
            if self.debug:
                self.config["project_description"] = "A software project with various components and functionality (debug mode)."
                self.console.print("[yellow]✔ Project description (debug mode): Using default description[/yellow]")
            else:
                self.config["project_description"] = self._generate_project_description(
                    structure, dependencies, descriptions
                )
        
        # Auto-generate entry file if empty
        if not self.config["entry_file"]:
            if self.debug:
                self.config["entry_file"] = "main.py"
                self.console.print("[yellow]✔ Entry file (debug mode): main.py[/yellow]")
            else:
                self.config["entry_file"] = self._generate_entry_file(
                    structure, dependencies, descriptions
                )
        
        # Auto-generate key features if empty
        if not self.config["key_features"]:
            if self.debug:
                self.config["key_features"] = "Core functionality, Easy to use, Well documented"
                self.console.print("[yellow]✔ Key features (debug mode): Using default features[/yellow]")
            else:
                self.config["key_features"] = self._generate_key_features(
                    structure, dependencies, descriptions
                )
        
        # Auto-generate additional info if empty
        if not self.config["additional_info"]:
            if self.debug:
                self.config["additional_info"] = "Additional project information will be available in production mode."
                self.console.print("[yellow]✔ Additional info (debug mode): Using default info[/yellow]")
            else:
                self.config["additional_info"] = self._generate_additional_info(
                    structure, dependencies, descriptions
                )
        
        # Generate logo
        if self.debug:
            logo_path = None
            self.console.print("[yellow]✔ Logo generation skipped (debug mode)[/yellow]")
        else:
            # Ask user if they want to generate logo
            if not self.silent:
                generate_logo_choice = self.console.input("[cyan]Do you want to generate a project logo? (y/n): [/cyan]").strip().lower()
                if generate_logo_choice not in ['y', 'yes', '是']:
                    logo_path = None
                    self.console.print("[yellow]✔ Logo generation skipped by user[/yellow]")
                else:
                    logo_path = generate_logo(
                        self.output_dir, descriptions, self.model_client, self.console
                    )
            else:
                # In silent mode, generate logo by default
                logo_path = generate_logo(
                    self.output_dir, descriptions, self.model_client, self.console
                )
        
        # Generate README content
        if self.debug:
            readme_content = self._generate_debug_readme_content(structure, dependencies, descriptions, logo_path)
        else:
            readme_content = self._generate_readme_content(
                structure, dependencies, descriptions, logo_path
            )
        # Save README
        readme_path = os.path.join(self.output_dir, "README.md")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)
            
        self.console.print(f"[bold green]✅ README generated successfully at {readme_path}[/bold green]")
        
        # 智能显示 GitHub 推广信息
        self._maybe_show_github_promotion()

    def _maybe_show_github_promotion(self):
        """智能显示 GitHub 推广信息，避免过度打扰用户"""
        import random
        import os
        
        # 检查用户是否禁用了推广
        if self.config.get("disable_github_promotion", False):
            return
            
        # 创建使用计数文件路径
        home_dir = os.path.expanduser("~")
        readmex_dir = os.path.join(home_dir, ".readmex")
        usage_file = os.path.join(readmex_dir, "usage_count")
        
        try:
            # 读取使用次数
            if os.path.exists(usage_file):
                with open(usage_file, "r") as f:
                    usage_count = int(f.read().strip())
            else:
                usage_count = 0
                
            # 更新使用次数
            usage_count += 1
            os.makedirs(readmex_dir, exist_ok=True)
            with open(usage_file, "w") as f:
                f.write(str(usage_count))
                
            # 智能显示逻辑：
            # 1. 第1次使用时必定显示
            # 2. 第3次使用时再次显示
            # 3. 之后每10次使用显示一次
            # 4. 或者有20%的随机概率显示
            should_show = (
                usage_count == 1 or  # 第1次使用
                usage_count == 3 or  # 第3次使用
                usage_count % 10 == 0 or  # 每10次使用
                random.random() < 0.2  # 20%随机概率
            )
            
            if should_show:
                self._show_github_promotion()
                
        except Exception:
            # 如果文件操作失败，使用简单的随机显示
            if random.random() < 0.15:  # 15%概率
                self._show_github_promotion()
    
    def _show_github_promotion(self):
        """显示 GitHub 推广信息"""
        if not self.silent:
            self.console.print("\n[dim]💡 如果 readmex 对你有帮助，请考虑给我们一个 star！[/dim]")
            
            # 询问用户是否要打开 GitHub
            open_github = self.console.input(
                "[cyan]是否现在打开 GitHub 仓库？ (y/N): [/cyan]"
            ).strip().lower()
            
            if open_github in ['y', 'yes', '是']:
                import webbrowser
                github_url = "https://github.com/aibox22/readmeX"
                webbrowser.open(github_url)
                self.console.print(f"[green]✔ 已在浏览器中打开: {github_url}[/green]")
            elif open_github == 'never':
                # 如果用户输入 'never'，则禁用推广
                self.config["disable_github_promotion"] = True
                self.console.print("[yellow]已禁用 GitHub 推广提示[/yellow]")

    def _load_configuration(self):
        """Load configuration from environment variables, config file, or user input."""
        from readmex.config import load_config, validate_config, CONFIG_FILE

        try:
            # First, validate and load existing configuration
            validate_config()
            config = load_config()

            # Update self.config with loaded values
            for key, value in config.items():
                if key in self.config and value:
                    self.config[key] = value

            # Set output directory if project_dir is available
            if self.project_dir:
                self.output_dir = os.path.join(self.project_dir, "readmex_output")
                os.makedirs(self.output_dir, exist_ok=True)
                self.console.print(
                    f"[green]✔ Configuration loaded from {CONFIG_FILE}[/green]"
                )
                self.console.print(
                    f"[green]✔ Output directory: {self.output_dir}[/green]"
                )

        except Exception as e:
            self.console.print(
                f"[yellow]Warning: Could not load configuration: {e}[/yellow]"
            )
            self.console.print(
                "[yellow]Will proceed with interactive configuration...[/yellow]"
            )

    def _get_basic_info(self):
        """
        Interactive input for basic information: project path and output directory
        """
        if self.silent:
            # 在静默模式下使用默认值
            current_dir = os.getcwd()
            if not self.project_dir:
                self.project_dir = current_dir
            self.console.print(f"[green]✔ Project path (silent mode): {self.project_dir}[/green]")
        else:
            self.console.print("[bold cyan]readmex - AI README Generator[/bold cyan]")
            self.console.print("Please configure basic information (press Enter to use default values)\n")

            # Get project path
            current_dir = os.getcwd()
            project_input = self.console.input(
                f"[cyan]Project Path[/cyan] (default: {current_dir}): "
            ).strip()

            if project_input:
                # Handle relative and absolute paths
                if os.path.isabs(project_input):
                    self.project_dir = project_input
                else:
                    self.project_dir = os.path.join(current_dir, project_input)
            else:
                self.project_dir = current_dir

        # Check if project path exists
        if not os.path.exists(self.project_dir):
            self.console.print(
                f"[red]Error: Project path '{self.project_dir}' does not exist[/red]"
            )
            exit(1)

        if not self.silent:
            self.console.print(f"[green]✔ Project path: {self.project_dir}[/green]")

        # Get output directory
        if self.silent:
            # 在静默模式下使用默认输出目录
            current_dir = os.getcwd()
            output_base = current_dir
        else:
            output_input = self.console.input(
                f"[cyan]Output Directory[/cyan] (default: {current_dir}): "
            ).strip()

            if output_input:
                # Handle relative and absolute paths
                if os.path.isabs(output_input):
                    output_base = output_input
                else:
                    output_base = os.path.join(current_dir, output_input)
            else:
                output_base = current_dir

        # Create readmex_output subdirectory under output directory
        self.output_dir = os.path.join(output_base, "readmex_output")

        # Create output directory
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            self.console.print(f"[green]✔ Output directory: {self.output_dir}[/green]")
        except Exception as e:
            self.console.print(
                f"[red]Error: Cannot create output directory '{self.output_dir}': {e}[/red]"
            )
            exit(1)

        if not self.silent:
            self.console.print()  # Empty line separator
            
            # Get additional project information
            self.console.print("[bold cyan]Additional Project Information[/bold cyan]")
            self.console.print(
                "Please provide additional information about your project (press Enter to skip):\n"
            )

            # Project language
            while True:
                readme_language = self.console.input(
                    "[cyan]Project Language[/cyan] (cn/en, or press Enter to use default language: en): [/cyan]"
                ).strip().lower()
                
                if not readme_language:
                    readme_language = "en"
                    break
                elif readme_language in ["cn", "en"]:
                    break
                else:
                    self.console.print("[red]Invalid language! Please enter 'cn' or 'en'[/red]")
            self.config["readme_language"] = readme_language
            
            # Project description
            user_description = self.console.input(
                "[cyan]Project Description[/cyan] (brief summary of what this project does, press Enter to auto-generate): "
            ).strip()

            if user_description:
                self.config["project_description"] = user_description
            else:
                self.console.print(
                    "[yellow]No description provided, will auto-generate based on project analysis...[/yellow]"
                )
                self.config["project_description"] = ""  # Will be generated later

            # Entry file
            user_entry_file = self.console.input(
                "[cyan]Entry File[/cyan] (main file to run the project, press Enter to auto-detect): "
            ).strip()

            if user_entry_file:
                self.config["entry_file"] = user_entry_file
            else:
                self.console.print(
                    "[yellow]No entry file specified, will auto-detect based on project analysis...[/yellow]"
                )
                self.config["entry_file"] = ""  # Will be generated later

            # Features
            user_features = self.console.input(
                "[cyan]Key Features[/cyan] (main features or capabilities, press Enter to auto-generate): "
            ).strip()

            if user_features:
                self.config["key_features"] = user_features
            else:
                self.console.print(
                    "[yellow]No features specified, will auto-generate based on project analysis...[/yellow]"
                )
                self.config["key_features"] = ""  # Will be generated later

            # Additional information
            user_additional_info = self.console.input(
                "[cyan]Additional Info[/cyan] (any other important information, press Enter to auto-generate): "
            ).strip()

            if user_additional_info:
                self.config["additional_info"] = user_additional_info
            else:
                self.console.print(
                    "[yellow]No additional info specified, will auto-generate based on project analysis...[/yellow]"
                )
                self.config["additional_info"] = ""  # Will be generated later

            self.console.print("\n[green]✔ Project information collected![/green]")
            self.console.print()  # Empty line separator
        else:
            # 在静默模式下，所有配置项都设为空，将自动生成
            self.config["project_description"] = ""
            self.config["entry_file"] = ""
            self.config["key_features"] = ""
            self.config["additional_info"] = ""
            self.console.print("[green]✔ Project information will be auto-generated (silent mode)[/green]")

    def _get_project_meta_info(self):
        if self.silent:
            # 在静默模式下跳过用户交互，使用空值（将自动生成）
            self.config["project_description"] = ""
            self.config["entry_file"] = ""
            self.config["key_features"] = ""
            self.config["additional_info"] = ""
            self.console.print("[green]✔ Project meta info will be auto-generated (silent mode)[/green]")
            return
            
        self.console.print(
            "Please provide additional project information (or press Enter to use defaults):"
        )

        # Project language
        while True:
            readme_language = self.console.input(
                "[cyan]Project Language (cn/en, or press Enter to use default language: en): [/cyan]"
            ).strip().lower()
            
            if not readme_language:
                readme_language = "en"
                break
            elif readme_language in ["cn", "en"]:
                break
            else:
                self.console.print("[red]Invalid language! Please enter 'cn' or 'en'[/red]")
        self.config["readme_language"] = readme_language

        # Project description
        user_description = self.console.input(
            "[cyan]Project Description (press Enter to auto-generate): [/cyan]"
        ).strip()

        if user_description:
            self.config["project_description"] = user_description
        else:
            self.console.print(
                "[yellow]No description provided, will auto-generate based on project analysis...[/yellow]"
            )
            self.config["project_description"] = ""  # Will be generated later
        user_entry_file = self.console.input(
            "[cyan]Entry File (press Enter to auto-detect): [/cyan]"
        ).strip()

        if user_entry_file:
            self.config["entry_file"] = user_entry_file
        else:
            self.console.print(
                "[yellow]No entry file specified, will auto-detect based on project analysis...[/yellow]"
            )
            self.config["entry_file"] = ""  # Will be generated later

        user_features = self.console.input(
            "[cyan]Key Features (press Enter to auto-generate): [/cyan]"
        ).strip()

        if user_features:
            self.config["key_features"] = user_features
        else:
            self.console.print(
                "[yellow]No features specified, will auto-generate based on project analysis...[/yellow]"
            )
            self.config["key_features"] = ""  # Will be generated later

        user_additional_info = self.console.input(
            "[cyan]Additional Information (press Enter to auto-generate): [/cyan]"
        ).strip()

        if user_additional_info:
            self.config["additional_info"] = user_additional_info
        else:
            self.console.print(
                "[yellow]No additional info specified, will auto-generate based on project analysis...[/yellow]"
            )
            self.config["additional_info"] = ""  # Will be generated later

    def _get_git_info(self):
        self.console.print("Gathering Git information...")

        # Check if GitHub username is already configured
        if self.config.get("github_username") and self.config["github_username"] != "":
            self.console.print(
                f"[green]✔ GitHub Username (from config): {self.config['github_username']}[/green]"
            )
            git_username_configured = True
        else:
            git_username_configured = False

        # Try to get repo info from git remote first (more reliable)
        repo_name_from_git = None
        try:
            # Use git remote get-url origin command
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                remote_url = result.stdout.strip()
                self.console.print(f"[cyan]Found git remote: {remote_url}[/cyan]")

                # Parse GitHub URL (supports both HTTPS and SSH)
                github_match = re.search(
                    r"github\.com[:/]([^/]+)/([^/\.]+)(?:\.git)?/?$", remote_url
                )

                if github_match:
                    if not git_username_configured:
                        self.config["github_username"] = github_match.group(1)
                        self.console.print(
                            f"[green]✔ GitHub Username (auto-detected): {self.config['github_username']}[/green]"
                        )
                        git_username_configured = True
                    repo_name_from_git = github_match.group(2)
                    self.config["repo_name"] = repo_name_from_git
                    # Set project_title based on repo_name if not already set
                    if not self.config.get("project_title"):
                        self.config["project_title"] = repo_name_from_git
                    self.console.print(f"[green]✔ Repository Name (auto-detected): {self.config['repo_name']}[/green]")
                    self.console.print(f"[green]✔ Project Title (auto-detected): {self.config['project_title']}[/green]")
                    return
                else:
                    self.console.print(
                        f"[yellow]Remote URL is not a GitHub repository: {remote_url}[/yellow]"
                    )
            else:
                self.console.print(
                    f"[yellow]Could not get git remote: {result.stderr.strip()}[/yellow]"
                )

        except subprocess.TimeoutExpired:
            self.console.print("[yellow]Git command timed out[/yellow]")
        except FileNotFoundError:
            self.console.print("[yellow]Git command not found[/yellow]")
        except Exception as e:
            self.console.print(f"[yellow]Could not get git remote: {e}[/yellow]")

        # Fallback: Try to get repo name from .git/config
        if not git_username_configured or not repo_name_from_git:
            try:
                git_config_path = os.path.join(self.project_dir, ".git", "config")
                if os.path.exists(git_config_path):
                    with open(git_config_path, "r") as f:
                        config_content = f.read()
                    url_match = re.search(
                        r"url =.*github.com[:/](.*?)/(.*?)\.git", config_content
                    )
                    if url_match:
                        if not git_username_configured:
                            self.config["github_username"] = url_match.group(1)
                            self.console.print(
                                f"[green]✔ GitHub Username (from .git/config): {self.config['github_username']}[/green]"
                            )
                            git_username_configured = True
                        if not repo_name_from_git:
                            repo_name_from_git = url_match.group(2)
                            self.config["repo_name"] = repo_name_from_git
                            # Set project_title based on repo_name if not already set
                            if not self.config.get("project_title"):
                                self.config["project_title"] = repo_name_from_git
                            self.console.print(f"[green]✔ Repository Name (from .git/config): {self.config['repo_name']}[/green]")
                            self.console.print(f"[green]✔ Project Title (from .git/config): {self.config['project_title']}[/green]")
                            return
            except Exception as e:
                self.console.print(f"[yellow]Could not read .git/config: {e}[/yellow]")

        # Only ask for missing information (skip in silent mode)
        if not git_username_configured:
            if self.silent:
                self.config["github_username"] = "your-username"
                self.console.print("[green]✔ GitHub Username (silent mode): your-username[/green]")
            else:
                self.console.print("[yellow]GitHub username not found, please enter manually:[/yellow]")
                self.config["github_username"] = self.console.input("[cyan]GitHub Username (default: your-username): [/cyan]") or "your-username"
        
        if not repo_name_from_git:
            if self.silent:
                self.config["repo_name"] = "your-repo"
                self.config["project_title"] = "your-repo"
                self.console.print("[green]✔ Repository Name (silent mode): your-repo[/green]")
                self.console.print("[green]✔ Project Title (silent mode): your-repo[/green]")
            else:
                self.console.print("[yellow]Repository name not found, please enter manually:[/yellow]")
                self.config["repo_name"] = self.console.input("[cyan]Repository Name (default: your-repo): [/cyan]") or "your-repo"
        
        # Set project_title based on repo_name if not already set
        if not self.config.get("project_title"):
            self.config["project_title"] = self.config["repo_name"]
            self.console.print(f"[green]✔ Project Title: {self.config['project_title']}[/green]")

    def _get_user_info(self):
        # Check which contact information is already configured
        configured_info = []
        missing_info = []

        contact_fields = [
            ("twitter_handle", "Twitter Handle", "@your_handle"),
            ("linkedin_username", "LinkedIn Username", "your-username"),
            ("email", "Email", "your.email@example.com"),
        ]

        for field_key, field_name, default_value in contact_fields:
            if (
                self.config.get(field_key)
                and self.config[field_key] != ""
                and self.config[field_key] != default_value
            ):
                configured_info.append((field_key, field_name, self.config[field_key]))
            else:
                missing_info.append((field_key, field_name, default_value))

        # Show already configured information
        if configured_info:
            self.console.print("[green]✔ Contact information (from config):[/green]")
            for field_key, field_name, value in configured_info:
                self.console.print(f"[green]  {field_name}: {value}[/green]")
        
        # Only ask for missing information (skip in silent mode)
        if missing_info:
            if self.silent:
                # 在静默模式下使用默认值
                for field_key, field_name, default_value in missing_info:
                    self.config[field_key] = default_value
                self.console.print("[green]✔ Contact information (silent mode): using defaults[/green]")
            else:
                self.console.print("Please enter missing contact information (or press Enter to use defaults):")
                for field_key, field_name, default_value in missing_info:
                    self.config[field_key] = self.console.input(f"[cyan]{field_name} (default: {default_value}): [/cyan]") or default_value

    def _get_project_dependencies(self):
        """Use DependencyAnalyzer to analyze project dependencies"""
        
        # Create dependency analyzer instance with primary language
        dependency_analyzer = DependencyAnalyzer(
            project_dir=self.project_dir,
            primary_language=self.primary_language,
            model_client=self.model_client,
            console=self.console
        )
        
        # Analyze project dependencies and return result
        return dependency_analyzer.analyze_project_dependencies(output_dir=self.output_dir)
    
    def _get_project_structure(self):
        self.console.print("[cyan]🤖 Generating project structure...[/cyan]")
        ignore_patterns = load_gitignore_patterns(self.project_dir)
        ignore_patterns = DEFAULT_IGNORE_PATTERNS + ignore_patterns
        self.console.print(f"Ignore patterns: {ignore_patterns}")
        structure = get_project_structure(self.project_dir, ignore_patterns)
        
        # 打印项目结构到控制台
        self.console.print("[bold green]📁 Project Structure:[/bold green]")
        self.console.print(structure)
        
        structure_path = os.path.join(self.output_dir, "project_structure.txt")
        with open(structure_path, "w", encoding="utf-8") as f:
            f.write(structure)
        self.console.print(
            f"[green]✔ Project structure saved to: {structure_path}[/green]"
        )
        return structure

    def _get_script_descriptions(self, max_workers=None):
        """
        Generate script descriptions using multithreading

        Args:
            max_workers (int): Maximum number of threads, if None will use config value
        """
        # Use config value if max_workers is not provided
        if max_workers is None:
            from readmex.config import get_max_workers
            max_workers = get_max_workers()
        self.console.print("[cyan]🤖 Generating script and document descriptions...[/cyan]")
        from readmex.config import (
            SCRIPT_PATTERNS,
            DOCUMENT_PATTERNS,
            DEFAULT_IGNORE_PATTERNS,
        )

        # 获取 gitignore 文件中的忽略模式
        gitignore_patterns = load_gitignore_patterns(self.project_dir)
        ignore_patterns = DEFAULT_IGNORE_PATTERNS + gitignore_patterns
        self.console.print(f"Ignore patterns: {ignore_patterns}")
        
                 # 获取主要语言的文件扩展名模式，并生成对应的文件模式
        language_patterns = []
        if self.primary_language and self.primary_language in self.language_analyzer.language_mapping:
            extensions = self.language_analyzer.language_mapping[self.primary_language]
            language_patterns = [f"*{ext}" for ext in extensions]
        
        # 如果没有检测到主要语言，使用默认的脚本模式，即 *.py
        if not language_patterns:
            language_patterns = SCRIPT_PATTERNS
        
        # 将主要语言模式和文档模式合并，以便生成更全面的文件描述
        all_patterns = language_patterns + DOCUMENT_PATTERNS
        self.console.print(f"Read patterns: {all_patterns}")
        filepaths = list(find_files(self.project_dir, all_patterns, ignore_patterns))

        if not filepaths:
            self.console.print(
                "[yellow]No script or document files found to process.[/yellow]"
            )
            return json.dumps({}, indent=2)

        table = Table(title="Files to be processed")
        table.add_column("File Path", style="cyan")
        for filepath in filepaths:
            table.add_row(os.path.relpath(filepath, self.project_dir))
        self.console.print(table)

        descriptions = {}
        descriptions_lock = Lock()  # Thread lock to protect shared dictionary

        def extract_python_from_ipynb(filepath):
            """Extract Python code from Jupyter notebook file"""
            try:
                import json
                with open(filepath, "r", encoding="utf-8") as f:
                    notebook = json.load(f)
                
                python_code = []
                for cell in notebook.get("cells", []):
                    if cell.get("cell_type") == "code":
                        source = cell.get("source", [])
                        if isinstance(source, list):
                            python_code.extend(source)
                        else:
                            python_code.append(source)
                
                return "".join(python_code)
            except Exception as e:
                self.console.print(f"[yellow]Warning: Failed to parse .ipynb file {filepath}: {e}[/yellow]")
                return ""

        def process_file(filepath):
            """Function to process a single file"""
            try:
                # Handle different file types
                if filepath.endswith('.ipynb'):
                    # Extract Python code from Jupyter notebook
                    content = extract_python_from_ipynb(filepath)
                    if not content.strip():
                        self.console.print(f"[yellow]Warning: No Python code found in {filepath}[/yellow]")
                        return False
                else:
                    # Regular text file
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()

                prompt = f"Analyze the following script and provide a concise summary. Focus on:\n1. Main purpose and functionality\n2. Key functions/methods and their roles\n3. Important features or capabilities\n\nScript content:\n{content}"
                description = self.model_client.get_answer(prompt)

                # Use lock to protect shared resource
                with descriptions_lock:
                    descriptions[os.path.relpath(filepath, self.project_dir)] = (
                        description
                    )

                return True
            except Exception as e:
                self.console.print(f"[red]Error processing {filepath}: {e}[/red]")
                return False

        # Use thread pool for concurrent processing
        with Progress() as progress:
            task = progress.add_task("[cyan]Generating...[/cyan]", total=len(filepaths))

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_filepath = {
                    executor.submit(process_file, filepath): filepath
                    for filepath in filepaths
                }

                # Process completed tasks
                for future in as_completed(future_to_filepath):
                    filepath = future_to_filepath[future]
                    try:
                        future.result()
                        progress.update(task, advance=1)
                    except Exception as e:
                        self.console.print(f"[red]Exception for {filepath}: {e}[/red]")
                        progress.update(task, advance=1)

        # Save script descriptions to output folder
        descriptions_json = json.dumps(descriptions, indent=2, ensure_ascii=False)
        if self.output_dir:
            descriptions_path = os.path.join(
                self.output_dir, "script_descriptions.json"
            )
            with open(descriptions_path, "w", encoding="utf-8") as f:
                f.write(descriptions_json)
            self.console.print(
                f"[green]✔ Script and document descriptions saved to: {descriptions_path}[/green]"
            )

        self.console.print(
            f"[green]✔ Script and document descriptions generated using {max_workers} threads.[/green]"
        )
        self.console.print(
            f"[green]✔ Processed {len(descriptions)} files successfully.[/green]"
        )
        return descriptions_json

    def _generate_project_description(self, structure, dependencies, descriptions):
        """
        Auto-generate project description based on project analysis

        Args:
            structure: Project structure string
            dependencies: Dependencies analysis string
            descriptions: File descriptions JSON string

        Returns:
            str: Generated project description
        """
        self.console.print(
            "[cyan]Auto-generating project description based on project analysis...[/cyan]"
        )

        try:
            prompt = f"""Based on the following project analysis, generate a concise and accurate project description (2-3 sentences maximum).

Project Structure:
```
{structure}
```

Dependencies:
```
{dependencies}
```

File Descriptions:
{descriptions}

Please analyze the project and provide:
1. What this project does (main purpose)
2. Key technologies/frameworks used
3. Primary functionality or features

Generate a brief, professional description that captures the essence of this project. Keep it under 100 words and focus on the core functionality.

Return only the description text, no additional explanations."""

            generated_description = self.model_client.get_answer(prompt)

            # Clean the generated description
            generated_description = generated_description.strip()
            if generated_description.startswith('"') and generated_description.endswith(
                '"'
            ):
                generated_description = generated_description[1:-1]

            self.console.print(
                f"[green]✔ Auto-generated description: {generated_description}[/green]"
            )
            return generated_description

        except Exception as e:
            self.console.print(
                f"[red]Failed to auto-generate project description: {e}[/red]"
            )
            return "A software project with various components and functionality."

    def _generate_entry_file(self, structure, dependencies, descriptions):
        """
        Auto-detect entry file based on project analysis

        Args:
            structure: Project structure string
            dependencies: Dependencies analysis string
            descriptions: File descriptions JSON string

        Returns:
            str: Detected entry file
        """
        self.console.print(
            "[cyan]Auto-detecting entry file based on project analysis...[/cyan]"
        )

        try:
            prompt = f"""Based on the following project analysis, identify the main entry file for this project.

Project Structure:
```
{structure}
```

Dependencies:
```
{dependencies}
```

File Descriptions:
{descriptions}

Please analyze the project and identify the main entry file that users would typically run to start the application. Look for:
1. Files with names like main.py, app.py, run.py, server.py, index.py
2. Files described as entry points or main applications
3. Files that contain main execution logic
4. Consider the dependencies to understand the project type

Return only the filename (e.g., "main.py", "app.py"), no path or additional explanations."""

            detected_entry = self.model_client.get_answer(prompt)

            # Clean the detected entry file
            detected_entry = detected_entry.strip()
            if detected_entry.startswith('"') and detected_entry.endswith('"'):
                detected_entry = detected_entry[1:-1]

            # Fallback to common names if detection fails
            if not detected_entry or len(detected_entry) > 50:
                detected_entry = "main.py"

            self.console.print(
                f"[green]✔ Auto-detected entry file: {detected_entry}[/green]"
            )
            return detected_entry

        except Exception as e:
            self.console.print(f"[red]Failed to auto-detect entry file: {e}[/red]")
            return "main.py"

    def _generate_key_features(self, structure, dependencies, descriptions):
        """
        Auto-generate key features based on project analysis

        Args:
            structure: Project structure string
            dependencies: Dependencies analysis string
            descriptions: File descriptions JSON string

        Returns:
            str: Generated key features
        """
        self.console.print(
            "[cyan]Auto-generating key features based on project analysis...[/cyan]"
        )

        try:
            prompt = f"""Based on the following project analysis, identify 3-5 key features or capabilities of this project.

Project Structure:
```
{structure}
```

Dependencies:
```
{dependencies}
```

File Descriptions:
{descriptions}

Please analyze the project and identify the main features or capabilities. Focus on:
1. Core functionality provided by the application
2. Key technologies or frameworks used
3. Important capabilities or services offered
4. Notable features that make this project useful

Return the features as a comma-separated list (e.g., "Feature 1, Feature 2, Feature 3"). Keep each feature concise (2-4 words)."""

            generated_features = self.model_client.get_answer(prompt)

            # Clean the generated features
            generated_features = generated_features.strip()
            if generated_features.startswith('"') and generated_features.endswith('"'):
                generated_features = generated_features[1:-1]

            self.console.print(
                f"[green]✔ Auto-generated features: {generated_features}[/green]"
            )
            return generated_features

        except Exception as e:
            self.console.print(f"[red]Failed to auto-generate key features: {e}[/red]")
            return "Core functionality, Easy to use, Well documented"

    def _generate_additional_info(self, structure, dependencies, descriptions):
        """
        Auto-generate additional information based on project analysis

        Args:
            structure: Project structure string
            dependencies: Dependencies analysis string
            descriptions: File descriptions JSON string

        Returns:
            str: Generated additional information
        """
        self.console.print(
            "[cyan]Auto-generating additional information based on project analysis...[/cyan]"
        )

        try:
            prompt = f"""Based on the following project analysis, generate additional important information about this project.

Project Structure:
```
{structure}
```

Dependencies:
```
{dependencies}
```

File Descriptions:
{descriptions}

Please analyze the project and provide additional useful information such as:
1. Notable technical details or architecture
2. Special requirements or prerequisites
3. Important usage notes or considerations
4. Unique aspects of the implementation

Generate 1-2 sentences of additional information that would be valuable for users. Keep it concise and informative.

Return only the additional information text, no explanations."""

            generated_info = self.model_client.get_answer(prompt)

            # Clean the generated info
            generated_info = generated_info.strip()
            if generated_info.startswith('"') and generated_info.endswith('"'):
                generated_info = generated_info[1:-1]

            self.console.print(
                f"[green]✔ Auto-generated additional info: {generated_info}[/green]"
            )
            return generated_info

        except Exception as e:
            self.console.print(
                f"[red]Failed to auto-generate additional info: {e}[/red]"
            )
            return ""

    def _generate_readme_content(
        self, structure, dependencies, descriptions, logo_path
    ):
        self.console.print("[cyan]🤖 Generating README content...[/cyan]")
        try:
            template_path = get_readme_template_path()
            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()
        except FileNotFoundError as e:
            self.console.print(f"[red]Error: {e}[/red]")
            return ""

        # Replace placeholders
        for key, value in self.config.items():
            if value:
                template = template.replace(f"{{{{{key}}}}}", value)
            else:
                # If value is empty, remove the line containing the placeholder
                template = re.sub(f".*{{{{{key}}}}}.*\n?", "", template)

        if self.config["github_username"] and self.config["repo_name"]:
            template = template.replace(
                "github_username/repo_name",
                f"{self.config['github_username']}/{self.config['repo_name']}",
            )
        else:
            # Remove all github-related badges and links if info is missing
            template = re.sub(
                r"\[\[(Contributors|Forks|Stargazers|Issues|project_license)-shield\]\]\[(Contributors|Forks|Stargazers|Issues|project_license)-url\]\n?",
                "",
                template,
            )

        # 添加详细的logo处理调试信息
        self.console.print(f"[cyan]DEBUG: Processing logo_path = {logo_path}[/cyan]")
        self.console.print(f"[cyan]DEBUG: output_dir = {self.output_dir}[/cyan]")
        
        try:
            if logo_path and os.path.exists(logo_path):
                self.console.print(f"[cyan]DEBUG: Logo file exists, processing relative path...[/cyan]")
                # Logo 和 README 都在同一个输出目录中，使用相对路径
                if logo_path is None:
                    raise ValueError(f"Logo path is None at line {1060}")
                if self.output_dir is None:
                    raise ValueError(f"Output directory is None at line {1060}")
                    
                relative_logo_path = os.path.relpath(logo_path, self.output_dir)
                # Convert Windows backslashes to forward slashes for web compatibility
                relative_logo_path = relative_logo_path.replace('\\', '/')
                self.console.print(f"[cyan]DEBUG: Relative logo path = {relative_logo_path}[/cyan]")
                
                # 替换整个logo img标签，使用新的属性
                template = re.sub(
                    r'<img src="images/logo\.png"[^>]*>',
                    f'<img src="{relative_logo_path}" alt="Logo" width="25%" height="auto">',
                    template
                )
                self.console.print(f"[green]✔ Logo template updated successfully[/green]")
            else:
                self.console.print(f"[yellow]WARNING: Logo path does not exist or is None, removing logo references[/yellow]")
                template = re.sub(r'<img src="images/logo.png".*>', "", template)
        except Exception as e:
            self.console.print(f"[red]ERROR in logo processing at line 1058-1066: {type(e).__name__}: {e}[/red]")
            self.console.print(f"[red]DEBUG: logo_path type = {type(logo_path)}, value = {logo_path}[/red]")
            self.console.print(f"[red]DEBUG: output_dir type = {type(self.output_dir)}, value = {self.output_dir}[/red]")
            # 发生错误时移除logo引用
            template = re.sub(r'<img src="images/logo.png".*>', "", template)
            raise

        # Remove screenshot section completely
        template = re.sub(
            r"\[\[Product Name Screen Shot\]\[product-screenshot\]\]\(https://example.com\)",
            "",
            template,
        )
        template = re.sub(
            r"\[product-screenshot\]: images/screenshot.png", "", template
        )
        # Remove any remaining screenshot references
        template = re.sub(
            r".*Product Name Screen Shot.*\n?", "", template
        )
        template = re.sub(
            r".*screenshot.*\n?", "", template, flags=re.IGNORECASE
        )

        # Prepare additional project information for the prompt
        additional_info = ""
        if self.config.get("project_description"):
            additional_info += (
                f"**Project Description:** {self.config['project_description']}\n"
            )
        if self.config.get("entry_file"):
            additional_info += f"**Entry File:** {self.config['entry_file']}\n"
        if self.config.get("key_features"):
            additional_info += f"**Key Features:** {self.config['key_features']}\n"
        if self.config.get("additional_info"):
            additional_info += (
                f"**Additional Information:** {self.config['additional_info']}\n"
            )

        # 构建logo处理指导
        logo_instruction = ""
        self.console.print(f"[cyan]DEBUG: Building logo instruction, logo_path = {logo_path}[/cyan]")
        
        try:
            if logo_path and os.path.exists(logo_path):
                self.console.print(f"[cyan]DEBUG: Building logo instruction with existing logo...[/cyan]")
                if logo_path is None:
                    raise ValueError(f"Logo path is None at line {1126}")
                if self.output_dir is None:
                    raise ValueError(f"Output directory is None at line {1126}")
                    
                relative_logo_path = os.path.relpath(logo_path, self.output_dir)
                self.console.print(f"[cyan]DEBUG: Logo instruction relative path = {relative_logo_path}[/cyan]")
                
                logo_instruction = f"""**IMPORTANT LOGO HANDLING INSTRUCTIONS:**
        - The template contains a project logo image reference: <img src="{relative_logo_path}" alt="Logo" width="25%" height="auto">
        - You MUST preserve this logo HTML tag exactly as provided in the template
        - Do NOT modify, remove, or change the logo image path, alt text, width, or height attributes
        - Do NOT convert the HTML img tag to Markdown image syntax
        - The logo should remain prominently displayed in the project header section
        - Keep the logo wrapped in the center-aligned div and link structure
        """
                self.console.print(f"[green]✔ Logo instruction built successfully[/green]")
            else:
                self.console.print(f"[yellow]WARNING: No logo available, building instruction without logo[/yellow]")
                logo_instruction = """**LOGO HANDLING:**
        - No logo is available for this project
        - Do not add any logo references or placeholder images
        - Remove any logo-related HTML tags from the template
        """
        except Exception as e:
            self.console.print(f"[red]ERROR in logo instruction building at line 1124-1140: {type(e).__name__}: {e}[/red]")
            self.console.print(f"[red]DEBUG: logo_path type = {type(logo_path)}, value = {logo_path}[/red]")
            self.console.print(f"[red]DEBUG: output_dir type = {type(self.output_dir)}, value = {self.output_dir}[/red]")
            # 发生错误时使用无logo的指导
            logo_instruction = """**LOGO HANDLING:**
        - No logo is available for this project
        - Do not add any logo references or placeholder images
        - Remove any logo-related HTML tags from the template
        """
            raise

        # 根据语言选择不同的提示词
        if self.config["readme_language"] == "cn":
            prompt = f"""你是一个README.md生成器，请用中文撰写README文件。你只需要返回README.md文件内容，不要输出任何其他内容。
            基于以下模板，请生成一个完整的README.md文件。
            根据用户提供的信息，填充任何缺失的信息。
            
            {logo_instruction}
            
            使用用户提供的信息来增强内容，特别是：
            - 项目描述和概述
            - 入口文件信息
            - 功能部分
            - 任何用户提供的信息

            **模板:**
            {template}

            **项目结构:**
            ```
            {structure}
            ```

            **依赖:**
            ```
            {dependencies}
            ```

            **脚本描述:**
            {descriptions}

            **额外项目信息:**
            {additional_info}

            请确保最终的README文件结构良好、专业，并适当包含所有用户提供的信息。
            再次强调，你需要生成由中文撰写的README.md文件，不要输出任何其他内容。
            """
        elif self.config["readme_language"] == "en":
            prompt = f"""You are a readme.md generator, please generate in English. You need to return the readme text directly without any other speech
            Based on the following template, please generate a complete README.md file. 
            Fill in any missing information based on the project context provided.

            {logo_instruction}

            Use the additional project information provided by the user to enhance the content, especially for:
            - Project description and overview
            - Entry file information
            - Features section
            - Any additional information provided by the user

            **Template:**
            {template}

            **Project Structure:**
            ```
            {structure}
            ```

            **Dependencies:**
            ```
            {dependencies}
            ```

            **Script Descriptions:**
            {descriptions}

            **Additional Project Information:**
            {additional_info}

            Please ensure the final README is well-structured, professional, and incorporates all the user-provided information appropriately.
        """
        else:
            # TODO: 支持其他语言
            # 默认使用英文模板
            prompt = f"""You are a readme.md generator, please generate in English. You need to return the readme text directly without any other speech
            Based on the following template, please generate a complete README.md file. 
            Fill in any missing information based on the project context provided.

            {logo_instruction}

            Use the additional project information provided by the user to enhance the content, especially for:
            - Project description and overview
            - Entry file information
            - Features section
            - Any additional information provided by the user

            **Template:**
            {template}

            **Project Structure:**
            ```
            {structure}
            ```

            **Dependencies:**
            ```
            {dependencies}
            ```

            **Script Descriptions:**
            {descriptions}

            **Additional Project Information:**
            {additional_info}

            Please ensure the final README is well-structured, professional, and incorporates all the user-provided information appropriately.
        """
            
        readme = self.model_client.get_answer(prompt)
        self.console.print("[green]✔ README content generated.[/green]")

        # Clean the generated content more carefully
        readme = readme.strip()

        # Remove markdown code block markers if present
        if readme.startswith("```"):
            lines = readme.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]  # Remove first line
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]  # Remove last line
            readme = "\n".join(lines)

        # Ensure the README includes reference links at the bottom
        # Check if reference links are missing and add them if needed
        if (
            "[contributors-shield]:" not in readme
            and self.config.get("github_username")
            and self.config.get("repo_name")
        ):
            self.console.print("[yellow]Adding missing reference links...[/yellow]")

            # Get the reference links from template
            try:
                template_path = get_readme_template_path()
                with open(template_path, "r", encoding="utf-8") as f:
                    template_content = f.read()

                # Extract reference links section from template
                ref_links_match = re.search(
                    r"<!-- MARKDOWN LINKS & IMAGES -->.*$", template_content, re.DOTALL
                )

                if ref_links_match:
                    ref_links = ref_links_match.group(0)

                    # Replace placeholders in reference links
                    ref_links = ref_links.replace(
                        "{{github_username}}", self.config["github_username"]
                    )
                    ref_links = ref_links.replace(
                        "{{repo_name}}", self.config["repo_name"]
                    )
                    if self.config.get("linkedin_username"):
                        ref_links = ref_links.replace(
                            "{{linkedin_username}}", self.config["linkedin_username"]
                        )

                    # Append reference links to README
                    if not readme.endswith("\n"):
                        readme += "\n"
                    readme += "\n" + ref_links

                    self.console.print("[green]✔ Reference links added.[/green]")

            except Exception as e:
                self.console.print(
                    f"[yellow]Could not add reference links: {e}[/yellow]"
                )

        return readme

    def _generate_debug_readme_content(self, structure, dependencies, descriptions, logo_path):
        """Generate README content in debug mode without LLM calls"""
        self.console.print("[yellow]Generating README content (debug mode - no LLM calls)...[/yellow]")
        try:
            template_path = get_readme_template_path()
            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()
        except FileNotFoundError as e:
            self.console.print(f"[red]Error: {e}[/red]")
            return ""

        # Replace placeholders with config values
        for key, value in self.config.items():
            if value:
                template = template.replace(f"{{{{{key}}}}}", value)
            else:
                # If value is empty, remove the line containing the placeholder
                template = re.sub(f".*{{{{{key}}}}}.*\n?", "", template)

        if self.config["github_username"] and self.config["repo_name"]:
            template = template.replace(
                "github_username/repo_name",
                f"{self.config['github_username']}/{self.config['repo_name']}",
            )
        else:
            # Remove all github-related badges and links if info is missing
            template = re.sub(
                r"\[\[(Contributors|Forks|Stargazers|Issues|project_license)-shield\]\]\[(Contributors|Forks|Stargazers|Issues|project_license)-url\]\n?",
                "",
                template,
            )

        # 添加详细的logo处理调试信息（调试模式）
        self.console.print(f"[cyan]DEBUG (debug mode): Processing logo_path = {logo_path}[/cyan]")
        self.console.print(f"[cyan]DEBUG (debug mode): output_dir = {self.output_dir}[/cyan]")
        
        try:
            if logo_path and os.path.exists(logo_path):
                self.console.print(f"[cyan]DEBUG (debug mode): Logo file exists, processing relative path...[/cyan]")
                # Logo 和 README 都在同一个输出目录中，使用相对路径
                if logo_path is None:
                    raise ValueError(f"Logo path is None at line {1315} (debug mode)")
                if self.output_dir is None:
                    raise ValueError(f"Output directory is None at line {1315} (debug mode)")
                    
                relative_logo_path = os.path.relpath(logo_path, self.output_dir)
                # Convert Windows backslashes to forward slashes for web compatibility
                relative_logo_path = relative_logo_path.replace('\\', '/')
                self.console.print(f"[cyan]DEBUG (debug mode): Relative logo path = {relative_logo_path}[/cyan]")
                
                # 替换整个logo img标签，使用新的属性
                template = re.sub(
                    r'<img src="images/logo\.png"[^>]*>',
                    f'<img src="{relative_logo_path}" alt="Logo" width="25%" height="auto">',
                    template
                )
                self.console.print(f"[green]✔ Logo template updated successfully (debug mode)[/green]")
            else:
                self.console.print(f"[yellow]WARNING (debug mode): Logo path does not exist or is None, removing logo references[/yellow]")
                template = re.sub(r'<img src="images/logo.png".*>', "", template)
        except Exception as e:
            self.console.print(f"[red]ERROR in debug mode logo processing at line 1313-1321: {type(e).__name__}: {e}[/red]")
            self.console.print(f"[red]DEBUG (debug mode): logo_path type = {type(logo_path)}, value = {logo_path}[/red]")
            self.console.print(f"[red]DEBUG (debug mode): output_dir type = {type(self.output_dir)}, value = {self.output_dir}[/red]")
            # 发生错误时移除logo引用
            template = re.sub(r'<img src="images/logo.png".*>', "", template)
            raise

        # Remove screenshot section
        template = re.sub(
            r"\[\[Product Name Screen Shot\]\[product-screenshot\]\]\(https://example.com\)",
            "",
            template,
        )
        template = re.sub(
            r"\[product-screenshot\]: images/screenshot.png", "", template
        )

        # Add debug mode notice
        debug_notice = "\n> **Note:** This README was generated in debug mode. For AI-enhanced content, run without --debug flag.\n"
        template = debug_notice + template

        self.console.print("[green]✔ README content generated (debug mode).[/green]")
        return template

    def _analyze_project_languages(self):
        """
        Analyze programming language distribution in the project
        """
        self.console.print("[cyan]🔍 Analyzing project language distribution...[/cyan]")

        try:
            # Use language analyzer to analyze the project (temporary variable)
            analysis_result = self.language_analyzer.analyze_project(
                self.project_dir
            )

            # Get primary language and save to self.primary_language
            self.primary_language = self.language_analyzer.get_primary_language(self.project_dir)

            # Display analysis results
            if analysis_result and analysis_result["languages"]:
                self.console.print("\n[bold green]📊 Project Language Distribution Analysis[/bold green]")

                # Create table to display language distribution
                table = Table(title="Language Distribution Details")
                table.add_column("Language", style="cyan", no_wrap=True)
                table.add_column("Files", justify="right", style="green")
                table.add_column("Lines", justify="right", style="blue")
                table.add_column("File %", justify="right", style="yellow")
                table.add_column("Line %", justify="right", style="magenta")

                for lang in analysis_result["languages"][:5]:  # Show top 5 languages
                    table.add_row(
                        lang["language"],
                        str(lang["files"]),
                        str(lang["lines"]),
                        f"{lang['file_percentage']:.1f}%",
                        f"{lang['line_percentage']:.1f}%",
                    )

                self.console.print(table)

                self.console.print(
                    f"[green]✔ Detected {analysis_result['summary']['total_languages']} programming languages[/green]"
                )
                if self.primary_language:
                    self.console.print(f"[green]✔ Primary language: {self.primary_language}[/green]")
            else:
                self.console.print("[yellow]⚠️  No programming language files detected[/yellow]")

        except Exception as e:
            self.console.print(f"[red]❌ Error during language analysis: {e}[/red]")
            self.primary_language = None
