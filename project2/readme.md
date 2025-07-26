
## project2 基于数字水印的图片泄露检测 
编程实现图片水印嵌入和提取（可依托开源项目二次开发），并进行鲁棒性测试，包括不限于翻转、平移、截取、调对比度等

得到结果，如下图所示：
cover


![01_cover](https://github.com/user-attachments/assets/dffd5ddb-ec95-4657-a9fd-19835c6fbd1e)


watermark


<img width="200" height="100" alt="02_watermark" src="https://github.com/user-attachments/assets/a1d7ad86-c77b-4583-9329-331e6fc5feb9" />


watermarked


![03_watermarked](https://github.com/user-attachments/assets/d04646c3-eb89-446a-baae-ed0e0ed9aa42)


extracted


<img width="200" height="100" alt="04_extracted" src="https://github.com/user-attachments/assets/a4f24df6-98ec-46c5-b58c-b683051f3884" />


下面测试鲁棒性


![05_blurring_attacked](https://github.com/user-attachments/assets/a4d440dc-098b-4bf8-a441-ad42f4fe0e1d)


![05_contrast_change_attacked](https://github.com/user-attachments/assets/c6111883-0f8d-4154-9b98-1cfbab87445b)


![05_cropping_attacked](https://github.com/user-attachments/assets/d4fc1a36-ffd2-4200-a662-c5c29bcc71d3)


![05_gaussian_noise_attacked](https://github.com/user-attachments/assets/caa3644b-6970-4886-81b3-0a4fdd22c1f8)


![05_rotation_attacked](https://github.com/user-attachments/assets/77c12b0f-555b-4160-bef7-0775dd5de67d)


![05_scaling_attacked](https://github.com/user-attachments/assets/24c538c6-0beb-4369-a3b3-672d2ff1ff60)



<img width="200" height="100" alt="06_blurring_extracted" src="https://github.com/user-attachments/assets/80806436-dca5-4f58-844a-df5710dd19ea" />


<img width="200" height="100" alt="06_contrast_change_extracted" src="https://github.com/user-attachments/assets/21d4a8e0-8fb2-4e86-8e82-f79960cf451c" />


<img width="200" height="100" alt="06_cropping_extracted" src="https://github.com/user-attachments/assets/64cf2e6f-7764-46c6-b30b-9f043057cab3" />


<img width="200" height="100" alt="06_gaussian_noise_extracted" src="https://github.com/user-attachments/assets/7cb1289e-5ea4-4b3d-bfed-f358ab92f3f0" /><img width="200" height="100" alt="06_rotation_extracted" src="https://github.com/user-attachments/assets/e87575fb-cfe2-4a4e-a6f7-97ee1f33fe1e" />


<img width="200" height="100" alt="06_scaling_extracted" src="https://github.com/user-attachments/assets/5138438c-c3d2-4ae2-a83b-6412a51adfb5" />


<img width="1500" height="1600" alt="07_robustness_test" src="https://github.com/user-attachments/assets/5351f6c8-3e0e-4323-b550-0eda6a447abc" />


